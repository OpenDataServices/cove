import pytest
import requests
from selenium import webdriver
from selenium.common.exceptions import NoSuchElementException
import time
import os


PREFIX_OCDS = os.environ.get('PREFIX_OCDS', '')
PREFIX_360 = os.environ.get('PREFIX_360', '')
if not PREFIX_360 and not PREFIX_OCDS:
    PREFIX_OCDS = '/ocds/'
    PREFIX_360 = '/360/'

PREFIX_LIST = [prefix for prefix in (PREFIX_OCDS, PREFIX_360) if prefix]


@pytest.fixture(scope="module")
def browser(request):
    browser = webdriver.Firefox()
    browser.implicitly_wait(3)
    request.addfinalizer(lambda: browser.quit())
    return browser


@pytest.fixture(scope="module")
def server_url(request, live_server):
    if 'CUSTOM_SERVER_URL' in os.environ:
        return os.environ['CUSTOM_SERVER_URL']
    else:
        return live_server.url
    

def test_index_page_banner(server_url, browser):
    if not PREFIX_360 or not PREFIX_OCDS:
        return
    browser.get(server_url)
    assert 'This tool is alpha. Please report any problems on GitHub issues.' in browser.find_element_by_tag_name('body').text
    if server_url == "http://dev.cove.opendataservices.coop/":
        assert 'This is a development site with experimental features. Do not rely on it.' in browser.find_element_by_tag_name('body').text
    

def test_index_page(server_url, browser):
    if not PREFIX_360 or not PREFIX_OCDS:
        return
    browser.get(server_url)
    assert 'CoVE' in browser.find_element_by_tag_name('body').text
    assert '360Giving Data Tool' in browser.find_element_by_tag_name('body').text
    assert 'Open Contracting Data Tool' in browser.find_element_by_tag_name('body').text
    assert 'Creating and using Open Data is made easier when there are good tools to help.' in browser.find_element_by_tag_name('body').text


@pytest.mark.parametrize(('link_text', 'expected_text', 'css_selector', 'url'), [
    # FIXME: Pick some text to lookg for on the OCP home page. Currently it's changing a lot.
    ('Open Contracting', '', 'div.homepage-title h1', 'http://www.open-contracting.org/'),
    ('Open Contracting Data Standard', 'Open Contracting Data Standard: Documentation', '#open-contracting-data-standard-documentation', 'http://standard.open-contracting.org/'),
    ])
def test_footer_ocds(server_url, browser, link_text, expected_text, css_selector, url):
    if not PREFIX_OCDS:
        return
    browser.get(server_url + PREFIX_OCDS)
    link = browser.find_element_by_link_text(link_text)
    href = link.get_attribute("href")
    assert url in href
    link.click()
    time.sleep(0.5)
    assert expected_text in browser.find_element_by_css_selector(css_selector).text


@pytest.mark.parametrize(('link_text', 'expected_text', 'css_selector', 'url'), [
    ('360Giving', 'We believe that with better information, grantmakers can be more effective and strategic decision-makers.', 'body.home', 'http://www.threesixtygiving.org/'),
    ('360Giving Data Standard', 'Standard', 'h1.entry-title', 'http://www.threesixtygiving.org/standard/'),
    ])
def test_footer_360(server_url, browser, link_text, expected_text, css_selector, url):
    if not PREFIX_360:
        return
    browser.get(server_url + PREFIX_360)
    link = browser.find_element_by_link_text(link_text)
    href = link.get_attribute("href")
    assert url in href
    link.click()
    time.sleep(0.5)
    assert expected_text in browser.find_element_by_css_selector(css_selector).text


def test_index_page_ocds(server_url, browser):
    if not PREFIX_OCDS:
        return
    browser.get(server_url + PREFIX_OCDS)
    assert 'Data Standard Validator' in browser.find_element_by_tag_name('body').text
    assert 'Using the validator' in browser.find_element_by_tag_name('body').text
    assert "'release'" in browser.find_element_by_tag_name('body').text
    assert "'record'" in browser.find_element_by_tag_name('body').text
    
    
def test_index_page_360(server_url, browser):
    if not PREFIX_360:
        return
    browser.get(server_url + PREFIX_360)
    assert '360Giving Data Tool' in browser.find_element_by_tag_name('body').text
    assert 'How to use the 360Giving Data Tool' in browser.find_element_by_tag_name('body').text
    assert 'Summary Spreadsheet - Excel' in browser.find_element_by_tag_name('body').text
    assert 'JSON built to the 360Giving JSON schema' in browser.find_element_by_tag_name('body').text
    assert 'Multi-table data package - Excel' in browser.find_element_by_tag_name('body').text
    assert '360 Giving' not in browser.find_element_by_tag_name('body').text
  
  
@pytest.mark.parametrize(('link_text', 'url'), [
    ('360Giving Data Standard guidence', 'http://www.threesixtygiving.org/standard/'),
    ('Excel', 'https://github.com/ThreeSixtyGiving/standard/raw/master/schema/summary-table/360-giving-schema-titles.xlsx'),
    ('CSV', 'https://github.com/ThreeSixtyGiving/standard/raw/master/schema/summary-table/360-giving-schema-titles.csv/grants.csv'),
    ('360Giving JSON schema', 'http://www.threesixtygiving.org/standard/reference/#toc-360giving-json-schemas'),
    ('Multi-table data package - Excel', 'https://github.com/ThreeSixtyGiving/standard/raw/master/schema/multi-table/360-giving-schema-fields.xlsx')
    ])
def test_index_page_360_links(server_url, browser, link_text, url):
    if not PREFIX_360:
        return
    link = browser.find_element_by_link_text(link_text)
    href = link.get_attribute("href")
    assert url in href


@pytest.mark.parametrize('prefix', PREFIX_LIST)
def test_common_index_elements(server_url, browser, prefix):
    if not PREFIX_360 or not PREFIX_OCDS:
        return
    browser.find_element_by_css_selector('#more-information').click()
    time.sleep(0.5)
    assert 'What happens to the data I provide to this site?' in browser.find_element_by_tag_name('body').text
    assert 'Why do you delete data after 7 days?' in browser.find_element_by_tag_name('body').text
    assert 'Why provide converted versions?' in browser.find_element_by_tag_name('body').text
    assert 'Terms & Conditions' in browser.find_element_by_tag_name('body').text
    assert 'Open Data Services' in browser.find_element_by_tag_name('body').text
    assert 'Open Data Services Co-operative' not in browser.find_element_by_tag_name('body').text
    assert '360 Giving' not in browser.find_element_by_tag_name('body').text


@pytest.mark.parametrize('prefix', PREFIX_LIST)
def test_terms_page(server_url, browser, prefix):
    browser.get(server_url + prefix + 'terms/')
    assert 'Open Data Services Co-operative Limited' in browser.find_element_by_tag_name('body').text
    assert 'Open Data Services Limited' not in browser.find_element_by_tag_name('body').text
    assert '360 Giving' not in browser.find_element_by_tag_name('body').text
    

@pytest.mark.parametrize('prefix', PREFIX_LIST)
def test_accordion(server_url, browser, prefix):
    browser.get(server_url + prefix)

    def buttons():
        return [b.is_displayed() for b in browser.find_elements_by_tag_name('button')]

    time.sleep(0.5)
    assert buttons() == [True, False, False]
    browser.find_element_by_partial_link_text('Link').click()
    browser.implicitly_wait(1)
    time.sleep(0.5)
    assert buttons() == [False, True, False]
    browser.find_element_by_partial_link_text('Paste').click()
    time.sleep(0.5)
    assert buttons() == [False, False, True]
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


@pytest.mark.parametrize(('prefix', 'source_filename', 'expected_text', 'conversion_successful'), [
    (PREFIX_OCDS, 'tenders_releases_2_releases.json', ['Download Files', 'Save or Share these results'], True),
    # Conversion should still work for files that don't validate against the schema
    (PREFIX_OCDS, 'tenders_releases_2_releases_invalid.json', ['Download Files', 'Validation Errors', "'id' is a required property"], True),
    # Test UTF-8 support
    (PREFIX_OCDS, 'utf8.json', 'Download Files', True),
    # But we expect to see an error message if a file is not well formed JSON at all
    (PREFIX_OCDS, 'tenders_releases_2_releases_not_json.json', 'not well formed JSON', False),
    (PREFIX_OCDS, 'tenders_releases_2_releases.xlsx', 'Download Files', True),
    (PREFIX_360, 'WellcomeTrust-grants_fixed_2_grants.json', ['Download Files',
                                                           'Save or Share these results',
                                                           'Unique Grant IDs: 2',
                                                           'Duplicate IDs: 2',
                                                           'Silent Signal',
                                                           'Showing 1 to 4 of 4 entries',
                                                           'Additional Fields',
                                                           'Data source',
                                                           "'24/07/2014' is not a 'date-time'",
                                                           "'13-03-2015' is not a 'date-time'"], True),
    # Test a 360 spreadsheet with titles, rather than fields
    (PREFIX_360, 'WellcomeTrust-grants_2_grants.xlsx', 'Download Files', True),
    # Test a 360 csv in cp1252 incoding
    (PREFIX_360, 'WellcomeTrust-grants_2_grants_cp1252.csv', 'Download Files', True),
    # Test a non-valid file.
    (PREFIX_360, 'paul-hamlyn-foundation-grants_dc.txt', 'We can only process json, csv and xlsx files', False),
    # Test a unconvertable spreadsheet (main sheet "grants" is missing)
    (PREFIX_360, 'basic.xlsx', 'We think you tried to supply a spreadsheet, but we failed to convert it to JSON.', False),
    # Test a unconvertable spreadsheet (main sheet "releases" is missing)
    (PREFIX_OCDS, 'WellcomeTrust-grants_2_grants.xlsx', 'We think you tried to supply a spreadsheet, but we failed to convert it to JSON.', False),
    # Test unconvertable JSON (main sheet "releases" is missing)
    (PREFIX_OCDS, 'unconvertable_json.json', 'could not be converted', False),
    (PREFIX_OCDS, 'full_record.json', ['Number of records', 'Validation Errors', 'compiledRelease', 'versionedRelease'], True),
    ])
def test_URL_input(server_url, browser, httpserver, source_filename, prefix, expected_text, conversion_successful):
    if not prefix:
        return
    with open(os.path.join('cove', 'fixtures', source_filename), 'rb') as fp:
        httpserver.serve_content(fp.read())
    if 'CUSTOM_SERVER_URL' in os.environ:
        # Use urls pointing to GitHub if we have a custom (probably non local) server URL
        source_url = 'https://raw.githubusercontent.com/OpenDataServices/cove/master/cove/fixtures/' + source_filename
    else:
        source_url = httpserver.url + '/' + source_filename

    browser.get(server_url + prefix)
    browser.find_element_by_partial_link_text('Link').click()
    time.sleep(0.5)
    browser.find_element_by_id('id_source_url').send_keys(source_url)
    browser.find_element_by_css_selector("#fetchURL > div.form-group > button.btn.btn-primary").click()
    check_url_input_result_page(server_url, browser, httpserver, source_filename, prefix, expected_text, conversion_successful)
    #refresh page to now check if tests still work after caching some data
    browser.get(browser.current_url)

    check_url_input_result_page(server_url, browser, httpserver, source_filename, prefix, expected_text, conversion_successful)
    
    browser.get(server_url + prefix + '?source_url=' + source_url)
    check_url_input_result_page(server_url, browser, httpserver, source_filename, prefix, expected_text, conversion_successful)


def check_url_input_result_page(server_url, browser, httpserver, source_filename, prefix, expected_text, conversion_successful):
    # We should still be in the correct app
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

    if prefix == PREFIX_OCDS:
        assert 'Data Standard Validator' in browser.find_element_by_tag_name('body').text
        # assert 'Release Table' in browser.find_element_by_tag_name('body').text
    elif prefix == PREFIX_360:
        assert '360Giving Data Tool' in browser.find_element_by_tag_name('body').text
        assert '360 Giving' not in browser.find_element_by_tag_name('body').text

    if conversion_successful:
        if source_filename.endswith('.json'):
            assert 'JSON (Original)' in body_text
            original_file = browser.find_element_by_link_text("JSON (Original)").get_attribute("href")
            if 'record' not in source_filename:
                converted_file = browser.find_element_by_link_text("Excel Spreadsheet (.xlsx) (Converted from Original)").get_attribute("href")
                assert "flattened.xlsx" in converted_file
        elif source_filename.endswith('.xlsx'):
            assert '(.xlsx) (Original)' in body_text
            original_file = browser.find_element_by_link_text("Excel Spreadsheet (.xlsx) (Original)").get_attribute("href")
            converted_file = browser.find_element_by_link_text("JSON (Converted from Original)").get_attribute("href")
            assert "unflattened.json" in converted_file
        elif source_filename.endswith('.csv'):
            assert '(.csv) (Original)' in body_text
            original_file = browser.find_element_by_link_text("CSV Spreadsheet (.csv) (Original)").get_attribute("href")
            converted_file = browser.find_element_by_link_text("JSON (Converted from Original)").get_attribute("href")
            assert "unflattened.json" in browser.find_element_by_link_text("JSON (Converted from Original)").get_attribute("href")

        assert source_filename in original_file
        assert '0 bytes' not in body_text
        # Test for Load New File button
        assert 'Load New File' in body_text

        original_file_response = requests.get(original_file)
        assert original_file_response.status_code == 200
        assert int(original_file_response.headers['content-length']) != 0

        if 'record' not in source_filename:
            converted_file_response = requests.get(converted_file)
            assert converted_file_response.status_code == 200
            assert int(converted_file_response.headers['content-length']) != 0


@pytest.mark.parametrize(('prefix'), PREFIX_LIST)
def test_URL_invalid_dataset_request(server_url, browser, prefix):
    # Test a badly formed hexadecimal UUID string
    browser.get(server_url + prefix + 'data/0')
    assert "We don't seem to be able to find the data you requested." in browser.find_element_by_tag_name('body').text
    # Test for well formed UUID that doesn't identify any dataset that exists
    browser.get(server_url + prefix + 'data/38e267ce-d395-46ba-acbf-2540cdd0c810')
    assert "We don't seem to be able to find the data you requested." in browser.find_element_by_tag_name('body').text
    assert '360 Giving' not in browser.find_element_by_tag_name('body').text
