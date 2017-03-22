import pytest
import requests
from django.conf import settings
from selenium import webdriver
from selenium.common.exceptions import NoSuchElementException
import time
import os


PREFIX_OCDS = os.environ.get('PREFIX_OCDS', '/')

BROWSER = os.environ.get('BROWSER', 'Firefox')

OCDS_SCHEMA_VERSIONS = settings.COVE_CONFIG['schema_version_choices']
OCDS_SCHEMA_VERSIONS_DISPLAY = list(display_url[0] for version, display_url in OCDS_SCHEMA_VERSIONS.items())


@pytest.fixture(scope="module")
def browser(request):
    browser = getattr(webdriver, BROWSER)()
    browser.implicitly_wait(3)
    request.addfinalizer(lambda: browser.quit())
    return browser


@pytest.fixture(scope="module")
def server_url(request, live_server):
    if 'CUSTOM_SERVER_URL' in os.environ:
        return os.environ['CUSTOM_SERVER_URL'] + PREFIX_OCDS
    else:
        return live_server.url + PREFIX_OCDS
    

@pytest.mark.parametrize(('link_text', 'expected_text', 'css_selector', 'url'), [
    ('Open Contracting', 'We connect governments', 'h1', 'http://www.open-contracting.org/'),
    ('Open Contracting Data Standard', 'Open Contracting Data Standard: Documentation', '#open-contracting-data-standard-documentation', 'http://standard.open-contracting.org/'),
    ])
def test_footer_ocds(server_url, browser, link_text, expected_text, css_selector, url):
    browser.get(server_url)
    footer = browser.find_element_by_id('footer')
    link = footer.find_element_by_link_text(link_text)
    href = link.get_attribute("href")
    assert url in href
    link.click()
    time.sleep(0.5)
    assert expected_text in browser.find_element_by_css_selector(css_selector).text


def test_index_page_ocds(server_url, browser):
    browser.get(server_url)
    assert 'Data Standard Validator' in browser.find_element_by_tag_name('body').text
    assert 'Using the validator' in browser.find_element_by_tag_name('body').text
    assert "'release'" in browser.find_element_by_tag_name('body').text
    assert "'record'" in browser.find_element_by_tag_name('body').text


@pytest.mark.parametrize(('css_id', 'link_text', 'url'), [
    ('introduction', 'schema', 'http://standard.open-contracting.org/latest/en/schema/'),
    ('introduction', 'Open Contracting Data Standard (OCDS)', 'http://standard.open-contracting.org/'),
    ('how-to-use', "'release' and 'record'", 'http://standard.open-contracting.org/latest/en/getting_started/releases_and_records/'),
    ('how-to-use', 'flattened serialization of OCDS', 'http://standard.open-contracting.org/latest/en/implementation/serialization/'),
    ('how-to-use', 'Open Contracting Data Standard', 'http://standard.open-contracting.org/')
    ])
def test_index_page_ocds_links(server_url, browser, css_id, link_text, url):
    browser.get(server_url)
    section = browser.find_element_by_id(css_id)
    link = section.find_element_by_link_text(link_text)
    href = link.get_attribute("href")
    assert url in href
    
    
def test_common_index_elements(server_url, browser):
    browser.get(server_url)
    browser.find_element_by_css_selector('#more-information .panel-title').click()
    time.sleep(0.5)
    assert 'What happens to the data I provide to this site?' in browser.find_element_by_tag_name('body').text
    assert 'Why do you delete data after 7 days?' in browser.find_element_by_tag_name('body').text
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
    assert 'Upload a file (.json, .csv, .xlsx)' in browser.find_elements_by_tag_name('label')[0].text
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


@pytest.mark.parametrize(('source_filename', 'expected_text', 'not_expected_text', 'conversion_successful'), [
    ('tenders_releases_2_releases.json', ['Convert', 'Schema'] + OCDS_SCHEMA_VERSIONS_DISPLAY, ['Schema Extensions'], True),
    ('tenders_releases_1_release_with_extensions.json', ['Schema Extensions',
                                                         'Contract Parties (Organization structure)',
                                                         'All the extensions above were applied',
                                                         'copy of the schema with extension',
                                                         'Validation Errors',
                                                         '\'buyer:id\' is missing but required'], ['fetching failed'], True),
    ('tenders_releases_1_release_with_invalid_extensions.json', ['Schema Extensions',
                                                                 'https://raw.githubusercontent.com/open-contracting/',
                                                                 'badprotocol://example.com',
                                                                 '400: bad request',
                                                                 'Only those extensions successfully fetched',
                                                                 'copy of the schema with extension',
                                                                 'Validation Errors'], ['All the extensions above were applied'], True),
    ('tenders_releases_1_release_with_all_invalid_extensions.json', ['Schema Extensions',
                                                                 'badprotocol://example.com',
                                                                 'None of the extensions above could be applied',
                                                                 '400: bad request'], ['copy of the schema with extension', 'Validation Errors'], True),
    ('ocds_release_nulls.json', ['Convert', 'Save or Share these results'], [], True),
    # Conversion should still work for files that don't validate against the schema
    ('tenders_releases_2_releases_invalid.json', ['Convert',
                                                  'Validation Errors',
                                                  "'id' is missing but required",
                                                  "Invalid 'uri' found"], [], True),
    ('tenders_releases_2_releases_codelists.json', ['oh no',
                                                    'GSINS'], [], True),
    # Test UTF-8 support
    ('utf8.json', 'Convert', [], True),
    # But we expect to see an error message if a file is not well formed JSON at all
    ('tenders_releases_2_releases_not_json.json', 'not well formed JSON', [], False),
    ('tenders_releases_2_releases.xlsx', ['Convert', 'Schema'] + OCDS_SCHEMA_VERSIONS_DISPLAY, [], True),
    ('badfile.json', 'Statistics can not produced', [], True),
    # Test unconvertable JSON (main sheet "releases" is missing)
    ('unconvertable_json.json', 'could not be converted', [], False),
    ('full_record.json', ['Number of records', 'Validation Errors', 'compiledRelease', 'versionedRelease'], [], True),
    ])
def test_URL_input(server_url, browser, httpserver, source_filename, expected_text, not_expected_text, conversion_successful):
    with open(os.path.join('cove_ocds', 'fixtures', source_filename), 'rb') as fp:
        httpserver.serve_content(fp.read())
    if 'CUSTOM_SERVER_URL' in os.environ:
        # Use urls pointing to GitHub if we have a custom (probably non local) server URL
        source_url = 'https://raw.githubusercontent.com/OpenDataServices/cove/master/cove/fixtures/' + source_filename
    else:
        source_url = httpserver.url + '/' + source_filename

    browser.get(server_url)
    browser.find_element_by_partial_link_text('Link').click()
    time.sleep(0.5)
    browser.find_element_by_id('id_source_url').send_keys(source_url)
    browser.find_element_by_css_selector("#fetchURL > div.form-group > button.btn.btn-primary").click()
    check_url_input_result_page(server_url, browser, httpserver, source_filename, expected_text, not_expected_text, conversion_successful)
    #refresh page to now check if tests still work after caching some data
    browser.get(browser.current_url)

    selected_examples = ['tenders_releases_2_releases_invalid.json', 'WellcomeTrust-grants_fixed_2_grants.xlsx', 'WellcomeTrust-grants_2_grants_cp1252.csv']

    if source_filename in selected_examples:
        check_url_input_result_page(server_url, browser, httpserver, source_filename, expected_text, not_expected_text, conversion_successful)
        browser.get(server_url + '?source_url=' + source_url)
        check_url_input_result_page(server_url, browser, httpserver, source_filename, expected_text, not_expected_text, conversion_successful)


def check_url_input_result_page(server_url, browser, httpserver, source_filename, expected_text, not_expected_text, conversion_successful):
    if source_filename.endswith('.json'):
        try:
            browser.find_element_by_name("flatten").click()
        except NoSuchElementException:
            pass
    body_text = browser.find_element_by_tag_name('body').text
    if isinstance(expected_text, str):
        expected_text = [expected_text]

    for text in expected_text:
        assert text in body_text

    for text in not_expected_text:
        assert text not in body_text

    assert 'Data Standard Validator' in browser.find_element_by_tag_name('body').text
    # assert 'Release Table' in browser.find_element_by_tag_name('body').text

    if conversion_successful:
        if source_filename.endswith('.json'):
            assert 'JSON (Original)' in body_text
            original_file = browser.find_element_by_link_text("JSON (Original)").get_attribute("href")
            if 'record' not in source_filename:
                converted_file = browser.find_element_by_partial_link_text("Excel Spreadsheet (.xlsx) (Converted from Original using schema version").get_attribute("href")
                assert "flattened.xlsx" in converted_file
        elif source_filename.endswith('.xlsx'):
            assert '(.xlsx) (Original)' in body_text
            original_file = browser.find_element_by_link_text("Excel Spreadsheet (.xlsx) (Original)").get_attribute("href")
            converted_file = browser.find_element_by_partial_link_text("JSON (Converted from Original using schema version").get_attribute("href")
            assert "unflattened.json" in converted_file
        elif source_filename.endswith('.csv'):
            assert '(.csv) (Original)' in body_text
            original_file = browser.find_element_by_link_text("CSV Spreadsheet (.csv) (Original)").get_attribute("href")
            converted_file = browser.find_element_by_partial_link_text("JSON (Converted from Original using schema version").get_attribute("href")
            assert "unflattened.json" in browser.find_element_by_partial_link_text("JSON (Converted from Original using schema version").get_attribute("href")

        assert source_filename in original_file
        assert '0 bytes' not in body_text
        # Test for Load New File button
        assert 'Load New File' in body_text

        original_file_response = requests.get(original_file)
        assert original_file_response.status_code == 200
        assert int(original_file_response.headers['content-length']) != 0

        if 'record' not in source_filename:
            converted_file_response = requests.get(converted_file)
            if source_filename == 'WellcomeTrust-grants_2_grants_titleswithoutrollup.xlsx':
                grant1 = converted_file_response.json()['grants'][1]
                assert grant1['recipientOrganization'][0]['department'] == 'Test data'
                assert grant1['classifications'][0]['title'] == 'Test'
            assert converted_file_response.status_code == 200
            assert int(converted_file_response.headers['content-length']) != 0


@pytest.mark.parametrize('warning_texts', [[], ['Some warning']])
@pytest.mark.parametrize('flatten_or_unflatten', ['flatten', 'unflatten'])
def test_flattentool_warnings(server_url, browser, httpserver, monkeypatch, warning_texts, flatten_or_unflatten):
    # If we're testing a remove server then we can't run this test as we can't
    # set up the mocks
    if 'CUSTOM_SERVER_URL' in os.environ:
        pytest.skip()
    # Actual input file doesn't matter, as we override
    # flattentool behaviour with a mock below
    if flatten_or_unflatten == 'flatten':
        source_filename = 'tenders_releases_2_releases.json'
    else:
        source_filename = 'tenders_releases_2_releases.xlsx'

    import flattentool
    import warnings
    from flattentool.exceptions import DataErrorWarning

    def mockunflatten(input_name, output_name, *args, **kwargs):
        with open(kwargs['cell_source_map'], 'w') as fp:
            fp.write('{}')
        with open(kwargs['heading_source_map'], 'w') as fp:
            fp.write('{}')
        with open(output_name, 'w') as fp:
            fp.write('{}')
            for warning_text in warning_texts:
                warnings.warn(warning_text, DataErrorWarning)

    def mockflatten(input_name, output_name, *args, **kwargs):
        with open(output_name + '.xlsx', 'w') as fp:
            fp.write('{}')
            for warning_text in warning_texts:
                warnings.warn(warning_text, DataErrorWarning)

    mocks = {
        'flatten': mockflatten,
        'unflatten': mockunflatten
    }
    monkeypatch.setattr(flattentool, flatten_or_unflatten, mocks[flatten_or_unflatten])

    with open(os.path.join('cove_ocds', 'fixtures', source_filename), 'rb') as fp:
        httpserver.serve_content(fp.read())
    if 'CUSTOM_SERVER_URL' in os.environ:
        # Use urls pointing to GitHub if we have a custom (probably non local) server URL
        source_url = 'https://raw.githubusercontent.com/OpenDataServices/cove/master/cove/fixtures/' + source_filename
    else:
        source_url = httpserver.url + '/' + source_filename

    browser.get(server_url + '?source_url=' + source_url)

    if source_filename.endswith('.json'):
        browser.find_element_by_name("flatten").click()

    body_text = browser.find_element_by_tag_name('body').text
    if len(warning_texts) == 0:
        assert 'conversion Errors' not in body_text
        assert 'Conversion Warnings' not in body_text
    else:
        assert warning_texts[0] in body_text
        assert 'Conversion Errors' in body_text
        assert 'conversion Warnings' not in body_text