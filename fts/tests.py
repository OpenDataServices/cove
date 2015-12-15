import pytest
import requests
from selenium import webdriver
import time
import os


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
    browser.get(server_url)
    assert 'This tool is alpha. Please report any problems on GitHub issues.' in browser.find_element_by_tag_name('body').text
    if server_url == "http://dev.cove.opendataservices.coop/":
        assert 'This is a development site with experimental features. Do not rely on it.' in browser.find_element_by_tag_name('body').text
    

def test_index_page(server_url, browser):
    browser.get(server_url)
    assert 'CoVE' in browser.find_element_by_tag_name('body').text
    assert '360Giving Data Tool' in browser.find_element_by_tag_name('body').text
    assert 'Open Contracting Data Tool' in browser.find_element_by_tag_name('body').text
    assert 'Creating and using Open Data is made easier when there are good tools to help.' in browser.find_element_by_tag_name('body').text


@pytest.mark.parametrize(('link_text', 'expected_text', 'css_selector', 'url'), [
    ('Open Contracting', 'What is Open Contracting?', 'div#page-what h1', 'http://www.open-contracting.org/'),
    ('Open Contracting Data Standard', 'OPEN CONTRACTING DATA STANDARD (OCDS) PROJECT SITE', 'h1.site-title', 'http://standard.open-contracting.org/'),
    ])
def test_footer_ocds(server_url, browser, link_text, expected_text, css_selector, url):
    browser.get(server_url + '/ocds/')
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
    browser.get(server_url + '/360/')
    link = browser.find_element_by_link_text(link_text)
    href = link.get_attribute("href")
    assert url in href
    link.click()
    time.sleep(0.5)
    assert expected_text in browser.find_element_by_css_selector(css_selector).text


def test_index_page_ocds(server_url, browser):
    browser.get(server_url + '/ocds/')
    assert 'Open Contracting Data Tool' in browser.find_element_by_tag_name('body').text
    assert 'How to use the Open Contracting Data Tool' in browser.find_element_by_tag_name('body').text
    assert "'release'" in browser.find_element_by_tag_name('body').text
    assert "'record'" in browser.find_element_by_tag_name('body').text
    
    
def test_index_page_360(server_url, browser):
    browser.get(server_url + '/360/')
    assert '360Giving Data Tool' in browser.find_element_by_tag_name('body').text
    assert 'How to use the 360Giving Data Tool' in browser.find_element_by_tag_name('body').text
    assert 'Summary Spreadsheet - Excel' in browser.find_element_by_tag_name('body').text
    assert 'JSON built to the 360Giving Data Standard JSON schema' in browser.find_element_by_tag_name('body').text
    assert 'Multi-table data package - Excel' in browser.find_element_by_tag_name('body').text
    assert '360 Giving' not in browser.find_element_by_tag_name('body').text
  
  
@pytest.mark.parametrize(('link_text', 'url'), [
    ('360Giving Data Standard guidence', 'http://www.threesixtygiving.org/standard/'),
    ('Excel', 'https://github.com/ThreeSixtyGiving/standard/raw/master/schema/summary-table/360-giving-schema-titles.xlsx'),
    ('CSV', 'https://github.com/ThreeSixtyGiving/standard/raw/master/schema/summary-table/360-giving-schema-titles.csv/grants.csv'),
    ('360Giving Data Standard JSON schema', 'http://www.threesixtygiving.org/standard/reference/#toc-json-schema'),
    ('Multi-table data package - Excel', 'https://github.com/ThreeSixtyGiving/standard/raw/master/schema/multi-table/360-giving-schema-fields.xlsx')
    ])
def test_index_page_360_links(server_url, browser, link_text, url):
    link = browser.find_element_by_link_text(link_text)
    href = link.get_attribute("href")
    assert url in href


@pytest.mark.parametrize('prefix', ['/ocds/', '/360/'])
def test_common_index_elements(server_url, browser, prefix):
    assert 'What happens to the data I provide to this site?' in browser.find_element_by_tag_name('body').text
    assert 'Why do you delete data after 7 days?' in browser.find_element_by_tag_name('body').text
    assert 'Why provide converted versions?' in browser.find_element_by_tag_name('body').text
    assert 'Terms & Conditions' in browser.find_element_by_tag_name('body').text
    assert 'Open Data Services' in browser.find_element_by_tag_name('body').text
    assert 'Open Data Services Co-operative' not in browser.find_element_by_tag_name('body').text
    assert '360 Giving' not in browser.find_element_by_tag_name('body').text


@pytest.mark.parametrize('prefix', ['/ocds/', '/360/'])
def test_terms_page(server_url, browser, prefix):
    browser.get(server_url + prefix + 'terms/')
    assert 'Open Data Services Co-operative Limited' in browser.find_element_by_tag_name('body').text
    assert 'Open Data Services Limited' not in browser.find_element_by_tag_name('body').text
    assert '360 Giving' not in browser.find_element_by_tag_name('body').text
    

@pytest.mark.parametrize('prefix', ['/ocds/', '/360/'])
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
    ('/ocds/', 'tenders_releases_2_releases.json', ['Download Files', 'Save or Share these results'], True),
    # Conversion should still work for files that don't validate against the schema
    ('/ocds/', 'tenders_releases_2_releases_invalid.json', ['Download Files', 'Validation Errors', "'id' is a required property"], True),
    # Test UTF-8 support
    ('/ocds/', 'utf8.json', 'Download Files', True),
    # But we expect to see an error message if a file is not well formed JSON at all
    ('/ocds/', 'tenders_releases_2_releases_not_json.json', 'not well formed JSON', False),
    ('/ocds/', 'tenders_releases_2_releases.xlsx', 'Download Files', True),
    ('/360/', 'WellcomeTrust-grants_fixed_2_grants.json', ['Download Files', 'Save or Share these results', 'Unique Grant IDs: 2', 'Duplicate IDs: 2'], True),
    # Test a 360 spreadsheet with titles, rather than fields
    ('/360/', 'WellcomeTrust-grants_2_grants.xlsx', 'Download Files', True),
    # Test a 360 csv in cp1252 incoding
    ('/360/', 'WellcomeTrust-grants_2_grants_cp1252.csv', 'Download Files', True),
    # Test a non-valid file.
    ('/360/', 'paul-hamlyn-foundation-grants_dc.txt', 'We can only process json, csv and xlsx files', False),
    # Test a unconvertable spreadsheet (main sheet "grants" is missing)
    ('/360/', 'basic.xlsx', 'We think you tried to supply a spreadsheet, but we failed to convert it to JSON.', False),
    # Test a unconvertable spreadsheet (main sheet "releases" is missing)
    ('/ocds/', 'WellcomeTrust-grants_2_grants.xlsx', 'We think you tried to supply a spreadsheet, but we failed to convert it to JSON.', False),
    # Test unconvertable JSON (main sheet "releases" is missing)
    ('/ocds/', 'unconvertable_json.json', 'could not be converted', False),
    ('/ocds/', 'full_record.json', ['Number of records', 'Validation Errors', 'compiledRelease', 'versionedRelease'], True),
    ])
def test_URL_input(server_url, browser, httpserver, source_filename, prefix, expected_text, conversion_successful):
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
    browser.refresh()
    check_url_input_result_page(server_url, browser, httpserver, source_filename, prefix, expected_text, conversion_successful)
    
    browser.get(server_url + prefix + '?source_url=' + source_url)
    check_url_input_result_page(server_url, browser, httpserver, source_filename, prefix, expected_text, conversion_successful)


def check_url_input_result_page(server_url, browser, httpserver, source_filename, prefix, expected_text, conversion_successful):
    # We should still be in the correct app
    body_text = browser.find_element_by_tag_name('body').text
    if isinstance(expected_text, str):
        expected_text = [expected_text]

    for text in expected_text:
        assert text in body_text

    if prefix == '/ocds/':
        assert 'Open Contracting Data Tool' in browser.find_element_by_tag_name('body').text
        # # Look for Release Table
        # assert 'Release Table' in browser.find_element_by_tag_name('body').text
    elif prefix == '/360/':
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


@pytest.mark.parametrize(('prefix'), [
    ('/ocds/'),
    ('/360/'),
    ])
def test_URL_invalid_dataset_request(server_url, browser, prefix):
    # Test a badly formed hexadecimal UUID string
    browser.get(server_url + prefix + 'data/0')
    assert "We don't seem to be able to find the data you requested." in browser.find_element_by_tag_name('body').text
    # Test for well formed UUID that doesn't identify any dataset that exists
    browser.get(server_url + prefix + 'data/38e267ce-d395-46ba-acbf-2540cdd0c810')
    assert "We don't seem to be able to find the data you requested." in browser.find_element_by_tag_name('body').text
    assert '360 Giving' not in browser.find_element_by_tag_name('body').text
