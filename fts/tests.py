import pytest
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
    

def test_index_page(server_url, browser):
    browser.get(server_url)
    assert 'CoVE' in browser.find_element_by_tag_name('body').text
    assert '360Giving Data Tool' in browser.find_element_by_tag_name('body').text
    assert 'Open Contracting Data Tool' in browser.find_element_by_tag_name('body').text
    assert 'Creating and using Open Data is made easier when there are good tools to help.' in browser.find_element_by_tag_name('body').text


def test_index_page_ocds(server_url, browser):
    browser.get(server_url + '/ocds/')
    assert 'Open Contracting Data Tool' in browser.find_element_by_tag_name('body').text
    assert 'How to use the Open Contracting Data Tool' in browser.find_element_by_tag_name('body').text
    
    
def test_index_page_360(server_url, browser):
    browser.get(server_url + '/360/')
    assert '360Giving Data Tool' in browser.find_element_by_tag_name('body').text
    assert 'How to use the 360Giving Data Tool' in browser.find_element_by_tag_name('body').text
    assert 'Summary Spreadsheet - Excel' in browser.find_element_by_tag_name('body').text
    assert 'JSON built to the 360Giving Data Standard JSON schema' in browser.find_element_by_tag_name('body').text
    assert 'Multi-table data package - Excel' in browser.find_element_by_tag_name('body').text
    assert '360 Giving' not in browser.find_element_by_tag_name('body').text


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
    ('/ocds/', 'tenders_releases_2_releases.json', 'Download Files', True),
    ('/ocds/', 'tenders_releases_2_releases.json', 'Save or Share these results', True),
    # Conversion should still work for files that don't validate against the schema
    ('/ocds/', 'tenders_releases_2_releases_invalid.json', 'Download Files', True),
    # Test UTF-8 support
    ('/ocds/', 'utf8.json', 'Download Files', True),
    # But we expect to see an error message if a file is not well formed JSON at all
    ('/ocds/', 'tenders_releases_2_releases_not_json.json', 'not well formed JSON', False),
    ('/ocds/', 'tenders_releases_2_releases.xlsx', 'Download Files', True),
    ('/360/', 'WellcomeTrust-grants_fixed_2_grants.json', 'Download Files', True),
    ('/360/', 'WellcomeTrust-grants_fixed_2_grants.json', 'Save or Share these results', True),
    # Test a 360 spreadsheet with titles, rather than fields
    ('/360/', 'WellcomeTrust-grants_2_grants.xlsx', 'Download Files', True),
    # Test a non-valid file. Currently csv is not supported
    ('/360/', 'paul-hamlyn-foundation-grants_dc.txt', 'We can only process json, csv and xlsx files', False),
    # Test a unconvertable spreadsheet (main sheet "grants" is missing)
    ('/360/', 'basic.xlsx', 'We think you tried to supply a spreadsheet, but we failed to convert it to JSON.', False),
    # Test a unconvertable spreadsheet (main sheet "releases" is missing)
    ('/ocds/', 'WellcomeTrust-grants_2_grants.xlsx', 'We think you tried to supply a spreadsheet, but we failed to convert it to JSON.', False),
    # Test unconvertable JSON (main sheet "releases" is missing)
    ('/ocds/', 'unconvertable_json.json', 'could not be converted', False),
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
    body_text = browser.find_element_by_tag_name('body').text
    assert expected_text in body_text
    
    # We should still be in the correct app
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
        elif source_filename.endswith('.xlsx'):
            assert '(.xlsx) (Original)' in body_text
        elif source_filename.endswith('.csv'):
            assert '(.csv) (Original)' in body_text


@pytest.mark.parametrize(('prefix'), [
    ('/ocds/'),
    ('/360/'),
    ])
def test_URL_invalid_dataset_request(server_url, browser, prefix):
    # Test a badly formed hexadecimal UUID string
    browser.get(server_url + prefix + 'data/0')
    assert "We don't seem to be able to find the data you requested." in browser.find_element_by_tag_name('body').text
    # Test for a dataset that does not exist in the dataset. Not sure how we specify a UUID that will never be used again tho!
    browser.get(server_url + prefix + 'data/be0c2fd7-108b-4d78-bae2-5a8a096a8273')
    assert "We don't seem to be able to find the data you requested." in browser.find_element_by_tag_name('body').text
    assert '360 Giving' not in browser.find_element_by_tag_name('body').text
