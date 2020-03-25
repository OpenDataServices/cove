import pytest
import requests
from selenium import webdriver
from selenium.common.exceptions import NoSuchElementException
import time
import os

import flattentool
import warnings
from flattentool.exceptions import DataErrorWarning
from selenium.webdriver.chrome.options import Options

BROWSER = os.environ.get('BROWSER', 'ChromeHeadless')

PREFIX_360 = os.environ.get('PREFIX_360', '/')


@pytest.fixture(scope="module")
def browser(request):
    if BROWSER == 'ChromeHeadless':
        chrome_options = Options()
        chrome_options.add_argument("--headless")
        browser = webdriver.Chrome(chrome_options=chrome_options)
    else:
        browser = getattr(webdriver, BROWSER)()
    browser.implicitly_wait(3)
    request.addfinalizer(lambda: browser.quit())
    return browser


@pytest.fixture(scope="module")
def server_url(request, live_server):
    if 'CUSTOM_SERVER_URL' in os.environ:
        return os.environ['CUSTOM_SERVER_URL'] + PREFIX_360
    else:
        return live_server.url + PREFIX_360


@pytest.mark.parametrize(('source_filename', 'expected_text', 'conversion_successful'), [
    ('fundingproviders-grants_fixed_2_grants.json', ['A file was downloaded from',
                                                  'This file contains 4 grants from 1 funder to 2 recipients awarded on 24/07/2014',
                                                  'The grants were awarded in GBP with a total value of £662,990 and individual awards ranging from £152,505 (lowest) to £178,990 (highest)',
                                                  'Convert to Spreadsheet',
                                                  'data does not use the 360Giving Standard 15 Errors',
                                                  'your data is not yet using the 360Giving standard',
                                                  'Incorrect Formats',
                                                  'Non-unique id values',
                                                  '100% of grants do not contain any beneficiary location fields',
                                                  'Grant identifiers:  2',
                                                  'Funder organisation identifiers:  1',
                                                  '360G-fundingproviders-000002/X/00/X'], True),
    ('fundingproviders-grants_broken_grants.json', ['data does not use the 360Giving Standard 15 Errors',
                                                 'Check your data 4 Grants',
                                                 'Funder organisation identifiers:  2',
                                                 'Recipient organisation identifiers:  2',
                                                 '360G-fundingproviders-000002/X/00/X'], True),
    ('fundingproviders-grants_2_grants.xlsx', ['This file contains 2 grants from 1 funder to 1 recipient',
                                            'The grants were awarded in GBP with a total value of £331,495',
                                            # check that there's no errors after the heading
                                            'This data could be read as 360Giving JSON data\nBefore checking',
                                            'data does not use the 360Giving Standard 7 Errors',
                                            'description is missing but required',
                                            'Sheet: grants Row: 2',
                                            'Check your data 2 Grants',
                                            'Funder organisation identifiers:  1',
                                            'Recipient organisation identifiers:  1',
                                            '360G-fundingproviders-000002/X/00/X'], True),
    # Test conversion warnings are shown
    ('tenders_releases_2_releases.xlsx', ['This data could not be read as 360Giving JSON data 5 Errors',
                                          'data does not use the 360Giving Standard 76 Errors',
                                          'You may have a duplicate Identifier: We couldn\'t merge these rows with the id "1": field "ocid" in sheet "items": one cell has the value: "PW-14-00627094", the other cell has the value: "PW-14-00629344"'
                                          ], True),
    # Test that titles that aren't in the rollup are converted correctly
    # (See @check_url_input_result_page).
    ('fundingproviders-grants_2_grants_titleswithoutrollup.xlsx', [], True),
    # Test a 360 csv in cp1252 encoding
    ('fundingproviders-grants_2_grants_cp1252.csv', ['This file contains 2 grants from 1 funder to 1 recipient',
                                                  'The grants were awarded in GBP with a total value of £331,495',
                                                  'This file is not \'utf-8\' encoded (it is cp1252 encoded)'], True),
    # Test a non-valid file.
    ('fundingtrust-grants_dc.txt', 'We can only process json, csv, ods and xlsx files', False),
    # Test a unconvertable spreadsheet (blank file)
    ('bad.xlsx', 'We think you tried to supply a spreadsheet, but we failed to convert it.', False),
    # Check that a file with a UTF-8 BOM converts correctly
    ('bom.csv', 'Grant identifiers:  1', True),
    ('nulls.json', [
        'is not a JSON array',
        'Date is not in the correct format',
        'Invalid code found in countryCode',
        'is not a number',
        'is not a string',
    ], True),
    ('decimal_amounts.csv', 'The grants were awarded in GBP with a total value of £7,000.7 and individual awards ranging from £1,000.1 (lowest) to £1,000.1 (highest).', True),
    ('decimal_amounts.json', 'The grants were awarded in GBP with a total value of £7,000.7 and individual awards ranging from £1,000.1 (lowest) to £1,000.1 (highest).', True),
    ('validation_errors-3.json', 'Something went wrong', False),
    ('badfile_all_validation_errors.json', [
        'description is missing but required (more info)',
        'id is missing but required within recipientOrganization (more info)',
        'Date is not in the correct format (more info)',
        '0 is not a JSON object',
        'amountAwarded is not a number. Check that the value is not null, and doesn’t contain any characters other than 0-9 and dot (.). Number values should not be in quotes.',
        'plannedDates is not a JSON array',
        'title is not a string. Check that the value is not null, and has quotes at the start and end. Escape any quotes in the value with \ (more info)',
        'Invalid \'uri\' found (more info)',
        'Invalid code found in currency (more info)',
        '[] is too short. You must supply at least one value, or remove the item entirely (unless it’s required).',

    ], True),
    ('badfile_all_validation_errors.xlsx', [
        'description is missing but required (more info)',
        'id is missing but required within recipientOrganization (more info)',
        'Date is not in the correct format (more info)',
        'Amount Awarded is not a number. Check that the value is not null, and doesn’t contain any characters other than 0-9 and dot (.). Number values should not be in quotes.',
        'Invalid \'uri\' found (more info)',
        'Invalid code found in Currency (more info)',
        '[] is too short. You must supply at least one value, or remove the item entirely (unless it’s required).',
        'bad date',
        'This should be a number',
        'This should be a uri',
        'bad currency',
    ], True),
    ('badfile_all_validation_errors_4_times.xlsx', [
        'Description is missing but required (more info)',
        'id is missing but required within recipientOrganization (more info)',
        'Date is not in the correct format (more info)',
        'Amount Awarded is not a number. Check that the value is not null, and doesn’t contain any characters other than 0-9 and dot (.). Number values should not be in quotes.',
        'Invalid \'uri\' found (more info)',
        'Invalid code found in Currency (more info)',
        '[] is too short. You must supply at least one value, or remove the item entirely (unless it’s required).',
        # Context dates should be ISO formatted
        '2019-06-01T00:00:00+00:00',
        'bad date 1',
        'bad date 2',
        'bad date 3',
        'bad date 4',
        'This should be a number',
        'This should be a uri 1',
        'This should be a uri 2',
        # 'This should be a uri 3',
        'This should be a uri 5',
        'This should be a uri 6',
        # 'This should be a uri 7',
        'bad currency 1',
        'bad currency 2',
        'bad currency 3',
        'bad currency 4',
    ], True),
])
def test_explore_360_url_input(server_url, browser, httpserver, source_filename, expected_text, conversion_successful):
    """
    TODO Test sequence: uploading JSON, files to Download only original, click convert,
    new http request, 'Data Summary' collapse. 'Download and Share' uncollapsed,
    converted files added.

    TODO Test file with grants in different currencies, check right text in 'Data Summary'

    TODO Test file with grants awarded on different dates, check right text in 'Data Summary'
    """
    with open(os.path.join('cove_360', 'fixtures', source_filename), 'rb') as fp:
        httpserver.serve_content(fp.read())
    if 'CUSTOM_SERVER_URL' in os.environ:
        # Use urls pointing to GitHub if we have a custom (probably non local) server URL
        source_url = 'https://raw.githubusercontent.com/OpenDataServices/cove/master/cove_360/fixtures/' + source_filename
    else:
        source_url = httpserver.url + PREFIX_360 + source_filename

    browser.get(server_url)
    browser.find_element_by_partial_link_text('Link').click()
    time.sleep(0.5)
    browser.find_element_by_id('id_source_url').send_keys(source_url)
    browser.find_element_by_css_selector("#fetchURL > div.form-group > button.btn.btn-primary").click()

    data_url = browser.current_url

    # Click and un-collapse all explore sections
    all_sections = browser.find_elements_by_class_name('panel-heading')
    for section in all_sections:
        if section.get_attribute('data-toggle') == "collapse" and section.get_attribute('aria-expanded') != 'true':
            section.click()
        time.sleep(0.5)

    # Do the assertions
    check_url_input_result_page(server_url, browser, httpserver, source_filename, expected_text, conversion_successful)

    #refresh page to now check if tests still work after caching some data
    browser.get(data_url)

    if conversion_successful:
        # Expand all sections with the expand all button this time
        browser.find_element_by_link_text('Expand all').click()
        time.sleep(0.5)

    # Do the assertions again
    check_url_input_result_page(server_url, browser, httpserver, source_filename, expected_text, conversion_successful)

    if conversion_successful:
        # Check that the advanced view loads without errors
        browser.get(data_url + '/advanced')
        assert 'Advanced view' in browser.find_element_by_tag_name('body').text


def check_url_input_result_page(server_url, browser, httpserver, source_filename, expected_text, conversion_successful):
    body_text = browser.find_element_by_tag_name('body').text
    if isinstance(expected_text, str):
        expected_text = [expected_text]

    for text in expected_text:
        assert text in body_text

    if source_filename == 'validation_errors-3.json':
        assert 'UNSAFE' not in body_text

    assert 'Data Quality Tool' in browser.find_element_by_class_name('title360').text
    assert '360 Giving' not in browser.find_element_by_tag_name('body').text

    if conversion_successful:
        if source_filename.endswith('.json'):
            assert 'Original file (json)' in body_text
            original_file = browser.find_element_by_link_text('Original file (json)').get_attribute("href")
        elif source_filename.endswith('.xlsx'):
            assert 'Original file (xlsx)' in body_text
            assert 'JSON (Converted from Original) ' in body_text
            original_file = browser.find_element_by_link_text('Original file (xlsx)').get_attribute("href")
            converted_file = browser.find_element_by_link_text("JSON (Converted from Original)").get_attribute("href")
            assert "unflattened.json" in converted_file
        elif source_filename.endswith('.csv'):
            assert 'Original file (csv)' in body_text
            original_file = browser.find_element_by_link_text('Original file (csv)').get_attribute("href")
            converted_file = browser.find_element_by_link_text("JSON (Converted from Original)").get_attribute("href")
            assert "unflattened.json" in browser.find_element_by_link_text("JSON (Converted from Original)").get_attribute("href")

        assert source_filename in original_file
        assert ' 0 bytes' not in body_text
        # Test for Load New File button
        assert 'Load New File' in body_text

        original_file_response = requests.get(original_file)
        assert original_file_response.status_code == 200
        assert int(original_file_response.headers['content-length']) != 0

        if source_filename.endswith('.xlsx') or source_filename.endswith('.csv'):
            converted_file_response = requests.get(converted_file)
            if source_filename == 'fundingproviders-grants_2_grants_titleswithoutrollup.xlsx':
                grant1 = converted_file_response.json()['grants'][1]
                assert grant1['recipientOrganization'][0]['department'] == 'Test data'
                assert grant1['classifications'][0]['title'] == 'Test'
            elif source_filename == 'bom.csv':
                assert converted_file_response.json()['grants'][0]['id'] == '42'
                assert 'This file is not \'utf-8\' encoded' not in body_text
            assert converted_file_response.status_code == 200
            assert int(converted_file_response.headers['content-length']) != 0


@pytest.mark.parametrize('iserror,warning_args', [
    (False, []),
    (True, ['Some warning', DataErrorWarning]),
    # Only warnings raised with the DataErrorWarning class should be shown
    # This avoids displaying messages like "Discarded range with reserved name"
    # https://github.com/OpenDataServices/cove/issues/444
    (False, ['Some warning'])
])
@pytest.mark.parametrize('flatten_or_unflatten', ['flatten', 'unflatten'])
def test_flattentool_warnings(server_url, browser, httpserver, monkeypatch, warning_args, flatten_or_unflatten, iserror):
    # If we're testing a remove server then we can't run this test as we can't
    # set up the mocks
    if 'CUSTOM_SERVER_URL' in os.environ:
        pytest.skip()
    if flatten_or_unflatten == 'flatten':
        source_filename = 'example.json'
    else:
        source_filename = 'example.xlsx'

    def mockunflatten(input_name, output_name, *args, **kwargs):
        with open(kwargs['cell_source_map'], 'w') as fp:
            fp.write('{}')
        with open(kwargs['heading_source_map'], 'w') as fp:
            fp.write('{}')
        with open(output_name, 'w') as fp:
            fp.write('{}')
            if warning_args:
                warnings.warn(*warning_args)

    def mockflatten(input_name, output_name, *args, **kwargs):
        with open(output_name + '.xlsx', 'w') as fp:
            fp.write('{}')
            if warning_args:
                warnings.warn(*warning_args)

    mocks = {
        'flatten': mockflatten,
        'unflatten': mockunflatten
    }
    monkeypatch.setattr(flattentool, flatten_or_unflatten, mocks[flatten_or_unflatten])

    # Actual input doesn't matter, as we override
    # flattentool behaviour with a mock below
    httpserver.serve_content('{}')
    source_url = httpserver.url + '/' + source_filename

    browser.get(server_url + '?source_url=' + source_url)

    if source_filename.endswith('.json'):
        browser.find_element_by_name("flatten").click()

    body_text = browser.find_element_by_tag_name('body').text
    assert 'Warning' not in body_text
    conversion_title = browser.find_element_by_id('conversion-title')
    if iserror:
        if flatten_or_unflatten == 'flatten':
            assert 'This data could not be read as 360Giving JSON data 1 Error' in body_text
        else:
            assert 'This data could not be read as 360Giving JSON data 1 Error' in body_text
        # should be a cross
        assert conversion_title.find_element_by_class_name('font-tick').get_attribute('class') == 'font-tick cross'
        conversion_title.click()
        time.sleep(0.5)
        assert warning_args[0] in browser.find_element_by_id('conversion-body').text
    else:
        if flatten_or_unflatten == 'flatten':
            assert 'This data could not be read as 360Giving JSON data 1 Error' not in body_text
        else:
            assert 'This data could not be read as 360Giving JSON data 1 Error' not in body_text
        # should be a tick
        assert conversion_title.find_element_by_class_name('font-tick').get_attribute('class') == 'font-tick tick'


@pytest.mark.parametrize(('link_text', 'expected_text', 'css_selector', 'url'), [
    ('360Giving', 'Open data for grantmaking', 'h2.hero__title', 'http://www.threesixtygiving.org/'),
    ('360Giving Data Standard', 'The 360Giving Data Standard', 'h2.cards-section__heading', 'http://www.threesixtygiving.org/standard/'),
    ])
def test_footer_360(server_url, browser, link_text, expected_text, css_selector, url):
    browser.get(server_url)
    link = browser.find_element_by_link_text(link_text)
    href = link.get_attribute("href")
    assert url in href
    link.click()
    time.sleep(0.5)
    assert expected_text in browser.find_element_by_css_selector(css_selector).text


def test_index_page_360(server_url, browser):
    browser.get(server_url)
    assert 'Data Quality Tool' in browser.find_element_by_class_name('title360').text
    assert 'How to use the 360Giving Data Quality Tool' in browser.find_element_by_tag_name('body').text
    assert 'Summary Spreadsheet - ' in browser.find_element_by_tag_name('body').text
    assert 'JSON built to the 360Giving JSON schema' in browser.find_element_by_tag_name('body').text
    assert 'Multi-table data package - Excel' in browser.find_element_by_tag_name('body').text
    assert '360 Giving' not in browser.find_element_by_tag_name('body').text


@pytest.mark.parametrize(('link_text', 'url'), [
    ('360Giving Data Standard guidance', 'http://www.threesixtygiving.org/standard/'),
    ('Excel', 'https://threesixtygiving-standard.readthedocs.io/en/latest/_static/summary-table/360-giving-schema-titles.xlsx'),
    ('CSV', 'https://threesixtygiving-standard.readthedocs.io/en/latest/templates-csv'),
    ('360Giving JSON schema', 'http://standard.threesixtygiving.org/en/latest/reference/#giving-json-schemas'),
    ('Multi-table data package - Excel', 'https://threesixtygiving-standard.readthedocs.io/en/latest/_static/multi-table/360-giving-schema-fields.xlsx')
    ])
def test_index_page_360_links(server_url, browser, link_text, url):
    browser.get(server_url)
    link = browser.find_element_by_link_text(link_text)
    href = link.get_attribute("href")
    assert url in href


def test_common_index_elements(server_url, browser):
    browser.get(server_url)
    browser.find_element_by_css_selector('#more-information .panel-title').click()
    time.sleep(0.5)
    assert 'What happens to the data I provide to this site?' in browser.find_element_by_tag_name('body').text
    assert 'Why do you delete data after seven days?' in browser.find_element_by_tag_name('body').text
    assert 'Why provide converted versions?' in browser.find_element_by_tag_name('body').text
    assert 'Terms & Conditions' in browser.find_element_by_tag_name('body').text
    assert 'Open Data Services' in browser.find_element_by_tag_name('body').text
    assert 'Open Data Services Co-operative' not in browser.find_element_by_tag_name('body').text
    assert '360 Giving' not in browser.find_element_by_tag_name('body').text


def test_terms_page(server_url, browser):
    browser.get(server_url + 'terms/')
    assert 'Open Data Services Co-operative Limited' in browser.find_element_by_tag_name('body').text
    assert 'Open Data Services Limited' not in browser.find_element_by_tag_name('body').text
    assert '360 Giving' not in browser.find_element_by_tag_name('body').text
    

def test_accordion(server_url, browser):
    browser.get(server_url)

    def buttons():
        return [b.is_displayed() for b in browser.find_elements_by_tag_name('button')]

    time.sleep(0.5)
    assert buttons() == [True, False, False]
    assert 'Upload a file' in browser.find_elements_by_tag_name('label')[0].text
    browser.find_element_by_partial_link_text('Link').click()
    browser.implicitly_wait(1)
    time.sleep(0.5)
    assert buttons() == [False, True, False]
    browser.find_element_by_partial_link_text('Paste').click()
    time.sleep(0.5)
    assert buttons() == [False, False, True]
    assert 'Paste (JSON only)' in browser.find_elements_by_tag_name('label')[2].text

    # Now test that the whole banner is clickable
    browser.find_element_by_id('headingOne').click()
    time.sleep(0.5)
    assert buttons() == [True, False, False]
    browser.find_element_by_id('headingTwo').click()
    time.sleep(0.5)
    assert buttons() == [False, True, False]
    browser.find_element_by_id('headingThree').click()
    time.sleep(0.5)
    assert buttons() == [False, False, True]


@pytest.mark.parametrize(('source_filename'), [
    ('fundingproviders-grants_fixed_2_grants.json'),
    ])
def test_error_modal(server_url, browser, httpserver, source_filename):
    with open(os.path.join('cove_360', 'fixtures', source_filename), 'rb') as fp:
        httpserver.serve_content(fp.read())
    if 'CUSTOM_SERVER_URL' in os.environ:
        # Use urls pointing to GitHub if we have a custom (probably non local) server URL
        source_url = 'https://raw.githubusercontent.com/OpenDataServices/cove/master/cove_360/fixtures/' + source_filename
    else:
        source_url = httpserver.url + '/' + source_filename

    browser.get(server_url)
    browser.find_element_by_partial_link_text('Link').click()
    time.sleep(0.5)
    browser.find_element_by_id('id_source_url').send_keys(source_url)
    browser.find_element_by_css_selector("#fetchURL > div.form-group > button.btn.btn-primary").click()

    # Click and un-collapse all explore sections
    all_sections = browser.find_elements_by_class_name('panel-heading')
    for section in all_sections:
        if section.get_attribute('data-toggle') == "collapse" and section.get_attribute('aria-expanded') != 'true':
            section.click()
        time.sleep(0.5)

    table_rows = browser.find_elements_by_css_selector('.validation-errors-format-1 tbody tr')
    assert len(table_rows) == 4

    browser.find_element_by_css_selector('a[data-target=".validation-errors-format-2"]').click()

    modal = browser.find_element_by_css_selector('.validation-errors-format-2')
    assert "in" in modal.get_attribute("class").split()
    modal_text = modal.text
    assert "24/07/2014" in modal_text
    assert "grants/0/awardDate" in modal_text

    browser.find_element_by_css_selector('div.modal.validation-errors-format-2 button.close').click()
    browser.find_element_by_css_selector('a[data-target=".usefulness-checks-2"]').click()

    modal_additional_checks = browser.find_element_by_css_selector('.usefulness-checks-2')
    assert "in" in modal_additional_checks.get_attribute("class").split()
    modal_additional_checks_text = modal_additional_checks.text
    assert "100% of grants do not have recipient organisation location information" in modal_additional_checks_text
    assert "grants/0/recipientOrganization/0/id" in modal_additional_checks_text
    table_rows = browser.find_elements_by_css_selector('.usefulness-checks-2 tbody tr')
    assert len(table_rows) == 4


@pytest.mark.parametrize(('source_filename', 'expected_text'), [
    ('fundingproviders-grants_fixed_2_grants.json', '360Giving JSON Package Schema')
    ])
def test_check_schema_link_on_result_page(server_url, browser, httpserver, source_filename, expected_text):
    with open(os.path.join('cove_360', 'fixtures', source_filename), 'rb') as fp:
        httpserver.serve_content(fp.read())
    if 'CUSTOM_SERVER_URL' in os.environ:
        # Use urls pointing to GitHub if we have a custom (probably non local) server URL
        source_url = 'https://raw.githubusercontent.com/OpenDataServices/cove/master/cove_360/fixtures/' + source_filename
    else:
        source_url = httpserver.url + '/' + source_filename

    browser.get(server_url)
    browser.find_element_by_partial_link_text('Link').click()
    time.sleep(0.5)
    browser.find_element_by_id('id_source_url').send_keys(source_url)
    browser.find_element_by_css_selector("#fetchURL > div.form-group > button.btn.btn-primary").click()
    
    # Click and un-collapse all explore sections
    all_sections = browser.find_elements_by_class_name('panel-heading')
    for section in all_sections:
        if section.get_attribute('data-toggle') == "collapse" and section.get_attribute('aria-expanded') != 'true':
            section.click()
        time.sleep(0.5)
    schema_link = browser.find_element_by_link_text(expected_text)
    schema_link.click()
    browser.find_element_by_id('giving-json-schemas')


@pytest.mark.parametrize(('data_url'), [
    'data/0',
    'data/324ea8eb-f080-43ce-a8c1-9f47b28162f3'
])
def test_url_invalid_dataset_request(server_url, browser, data_url):
    # Test a badly formed hexadecimal UUID string
    browser.get(server_url + data_url)
    assert "We don't seem to be able to find the data you requested." in browser.find_element_by_tag_name('body').text
    # Test for well formed UUID that doesn't identify any dataset that exists
    browser.get(server_url + 'data/38e267ce-d395-46ba-acbf-2540cdd0c810')
    assert "We don't seem to be able to find the data you requested." in browser.find_element_by_tag_name('body').text
    assert '360 Giving' not in browser.find_element_by_tag_name('body').text
    #363 - Tests there is padding round the 'go to home' button
    success_button = browser.find_element_by_class_name('success-button')
    assert success_button.value_of_css_property('padding-bottom') == '20px'


def test_500_error(server_url, browser):
    browser.get(server_url + 'test/500')
    # Check that our nice error message is there
    assert 'Something went wrong' in browser.find_element_by_tag_name('body').text
    # Check for the exclamation icon
    # This helps to check that the theme including the css has been loaded
    # properly
    icon_span = browser.find_element_by_class_name('panel-danger').find_element_by_tag_name('span')
    assert 'Glyphicons Halflings' in icon_span.value_of_css_property('font-family')
    assert icon_span.value_of_css_property('color') == 'rgba(255, 255, 255, 1)'


def test_common_errors_page(server_url, browser):
    browser.get(server_url + 'common_errors/')
    assert "Common Errors" in browser.find_element_by_tag_name('h2').text
    assert '360 Giving' not in browser.find_element_by_tag_name('body').text


@pytest.mark.parametrize(('anchor_text'), [
    ('uri'),
    ('date-time'),
    ('required'),
    ('enum'),
    ('string'),
    ('number')
    ])
def test_common_errors_page_anchors(server_url, browser, anchor_text):
    # Checks we have sections for each our error messages
    browser.get(server_url + 'common_errors/')
    browser.find_element_by_id(anchor_text)


def test_favicon(server_url, browser):
    browser.get(server_url)
    # we should not have a favicon link just now
    with pytest.raises(NoSuchElementException):
        browser.find_element_by_xpath("//link[@rel='icon']")


def test_explore_360_sample_data_link(server_url, browser):
    browser.get(server_url)
    browser.find_element_by_partial_link_text('loading some sample data.').click()
    time.sleep(0.5)
    body_text = browser.find_element_by_tag_name('body').text

    assert 'Summary: Your data at a glance' in body_text
    assert 'Sorry, we can\'t process that data' not in body_text
    # Show sample data link in the home page only
    with pytest.raises(NoSuchElementException):
        browser.find_element_by_partial_link_text('loading some sample data.')
