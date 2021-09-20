import os
import time
import pytest
import requests
from selenium import webdriver
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.chrome.options import Options

BROWSER = os.environ.get('BROWSER', 'ChromeHeadless')


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
        return os.environ['CUSTOM_SERVER_URL']
    else:
        return live_server.url


def test_accordion(server_url, browser):
    browser.get(server_url)

    def buttons():
        return [b.is_displayed() for b in browser.find_elements_by_tag_name('button')]

    time.sleep(0.5)
    assert buttons() == [True, False, False]
    assert 'Upload a file (.csv, .xlsx, .xml)' in browser.find_elements_by_tag_name('label')[0].text
    browser.find_element_by_partial_link_text('Link').click()
    browser.implicitly_wait(1)
    time.sleep(0.5)
    assert buttons() == [False, True, False]
    browser.find_element_by_partial_link_text('Paste').click()
    time.sleep(0.5)
    assert buttons() == [False, False, True]
    assert 'Paste (XML only)' in browser.find_elements_by_tag_name('label')[2].text

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


def test_index_page_iati(server_url, browser):
    browser.get(server_url)
    assert 'How to use IATI CoVE' in browser.find_element_by_tag_name('body').text
    assert 'XML - according to version 2.03 of the IATI schema' in browser.find_element_by_tag_name('body').text
    assert 'Spreadsheet - Excel, CSV (UTF-8, Windows-1252 and ISO-8859-1 encodings supported) - see sample data' in browser.find_element_by_tag_name('body').text


@pytest.mark.parametrize(('link_text', 'url'), [
    ('IATI schema', 'http://reference.iatistandard.org/203/schema/')
    ])
def test_index_page_iati_links(server_url, browser, link_text, url):
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


@pytest.mark.parametrize(('source_filename', 'expected_text', 'conversion_successful'), [
    ('example.xml', ['Valid against Schema'], False),
    ('basic_iati_unordered_valid.xlsx', ['Valid against Schema'], True),
    ('basic_iati_unordered_invalid_iso_dates.xlsx', ['Invalid against Schema', 'Path: iati-activity/0/activity-date/@iso-date Line: 17', 'Path: iati-activity/1/activity-date/@iso-date Line: 54'], True),
    ('basic_iati_org_valid.xlsx', ['Valid against Schema'], True),
    ('bad.xml', ['We think you tried to upload a XML file'], False),
    ('bad_spaces.csv', ['Converted to XML 2 Errors'], True),
    ('basic_iati_ruleset_errors.xml', ['Invalid against Schema 13 Errors', '20140101',
                                       '\'budget\': Missing child element(s), expected is value',
                                       'Ruleset Errors 13 Errors',
                                       'Start date (2010-01-01) must be before end date (2009-01-01)',
                                       'Start dates must be chronologically before end dates',
                                       'Percentages must sum to 100%',
                                       'Elements must use a valid format',
                                       'Actual dates must be in the past',
                                       'Elements are mandatory',
                                       'Sector must be specified'], False),
    # We should not server error when there's fields not in the schema
    ('not_iati.csv', ['Data Supplied', 'Invalid against Schema'], True),
    ('namespace_good.xlsx', ['Converted to XML', 'Invalid against Schema', '2 Errors'], True),
    ('namespace_bad.xlsx', ['Converted to XML', 'Invalid against Schema', "'iati-activity', attribute 'test2': The attribute 'test2' is not allowed.", '3 Errors'], True),
])
def test_explore_iati_url_input(server_url, browser, httpserver, source_filename, expected_text, conversion_successful):
    with open(os.path.join('cove_iati', 'fixtures', source_filename), 'rb') as fp:
        httpserver.serve_content(fp.read())
    if 'CUSTOM_SERVER_URL' in os.environ:
        # Use urls pointing to GitHub if we have a custom (probably non local) server URL
        source_url = 'https://raw.githubusercontent.com/OpenDataServices/cove/live/cove_iati/fixtures/' + source_filename
    else:
        source_url = httpserver.url + '/' + source_filename

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
            browser.execute_script("arguments[0].scrollIntoView();", section)
            section.click()
        time.sleep(0.5)

    # Do the assertions
    check_url_input_result_page(server_url, browser, httpserver, source_filename, expected_text, conversion_successful)

    #refresh page to now check if tests still work after caching some data
    browser.get(data_url)

    # Expand all sections with the expand all button this time
    try:
        browser.find_element_by_link_text('Expand all').click()
        time.sleep(0.5)
    except NoSuchElementException:
        pass

    # Do the assertions again
    check_url_input_result_page(server_url, browser, httpserver, source_filename, expected_text, conversion_successful)


def check_url_input_result_page(server_url, browser, httpserver, source_filename, expected_text, conversion_successful):
    body_text = browser.find_element_by_tag_name('body').text
    if isinstance(expected_text, str):
        expected_text = [expected_text]

    for text in expected_text:
        assert text in body_text

    if conversion_successful:
        assert 'Converted to XML' in body_text

    if source_filename == 'namespace_good.xlsx':
        converted_file = browser.find_element_by_link_text("XML (Converted from Original)").get_attribute("href")
        assert requests.get(converted_file).text == '''<?xml version='1.0' encoding='utf-8'?>
<iati-activities>
  <!--Data generated by IATI CoVE. Built by Open Data Services Co-operative: http://iati.cove.opendataservices.coop/-->
  <iati-activity xmlns:myns="http://example.org" myns:test2="3">
    <myns:test>1</myns:test>
    <test2>2</test2>
  </iati-activity>
</iati-activities>
'''

    if source_filename == 'basic_iati_org_valid.xlsx':
        converted_file = browser.find_element_by_link_text("XML (Converted from Original)").get_attribute("href")
        assert requests.get(converted_file).text == '''<?xml version='1.0' encoding='utf-8'?>
<iati-organisations version="2.03">
  <!--Data generated by IATI CoVE. Built by Open Data Services Co-operative: http://iati.cove.opendataservices.coop/-->
  <iati-organisation default-currency="EUR" last-updated-datetime="2014-09-10T07:15:37Z" xml:lang="en">
    <organisation-identifier>AA-AAA-123456789</organisation-identifier>
    <name>
      <narrative>Organisation name</narrative>
    </name>
    <reporting-org ref="AA-AAA-123456789" type="40">
      <narrative>Organisation name</narrative>
    </reporting-org>
    <document-link format="application/vnd.oasis.opendocument.text" url="http://www.example.org/docs/report_en.odt">
      <title>
        <narrative>Annual Report 2013</narrative>
      </title>
      <category code="B01"/>
      <language code="en"/>
      <document-date iso-date="2014-02-05"/>
      <recipient-country code="AF"/>
    </document-link>
    <document-link format="application/vnd.oasis.opendocument.text" url="http://www.example.org/docs/report_fr.odt">
      <title>
        <narrative xml:lang="fr">Rapport annuel 2013</narrative>
      </title>
      <category code="B01"/>
      <language code="fr"/>
      <document-date iso-date="2014-02-05"/>
      <recipient-country code="AF"/>
    </document-link>
  </iati-organisation>
</iati-organisations>
'''


def test_rulesets_table_toggle(server_url, browser, httpserver):
    with open(os.path.join('cove_iati', 'fixtures', 'basic_iati_ruleset_errors.xml'), 'rb') as fp:
        httpserver.serve_content(fp.read())
    if 'CUSTOM_SERVER_URL' in os.environ:
        # Use urls pointing to GitHub if we have a custom (probably non local) server URL
        source_url = ('https://raw.githubusercontent.com/OpenDataServices/cove/'
                      'live/cove_iati/fixtures/basic_iati_ruleset_errors.xml')
    else:
        source_url = httpserver.url + '/basic_iati_ruleset_errors.xml'

    browser.get(server_url)
    browser.find_element_by_partial_link_text('Link').click()
    time.sleep(0.5)
    browser.find_element_by_id('id_source_url').send_keys(source_url)
    browser.find_element_by_css_selector('#fetchURL > div.form-group > button.btn.btn-primary').click()

    # Click and un-collapse all explore sections
    all_sections = browser.find_elements_by_class_name('panel-heading')
    for section in all_sections:
        if section.get_attribute('data-toggle') == 'collapse':
            if section.get_attribute('aria-expanded') != 'true':
                browser.execute_script('arguments[0].scrollIntoView();', section)
                section.click()
        time.sleep(0.5)

    toggle_button = browser.find_element_by_name('ruleset-table-toggle')
    table_header = browser.find_element_by_css_selector('table#ruleset-by-rule thead tr')
    header_html = ''.join(table_header.get_attribute('innerHTML').strip().split())

    assert toggle_button.text == 'See same results by activity'
    assert browser.find_element_by_id('ruleset-by-rule').is_displayed()
    assert not browser.find_element_by_id('ruleset-by-activity').is_displayed()
    assert header_html == '<th>Ruleset</th><th>Rule</th><th>Activity</th><th>Explanation</th><th>Path</th>'

    toggle_button.click()
    time.sleep(0.5)
    toggle_button = browser.find_element_by_name('ruleset-table-toggle')
    table_header = browser.find_element_by_css_selector('table#ruleset-by-activity thead tr')
    header_html = ''.join(table_header.get_attribute('innerHTML').strip().split())

    assert toggle_button.text == 'See same results by ruleset'
    assert browser.find_element_by_id('ruleset-by-activity').is_displayed()
    assert not browser.find_element_by_id('ruleset-by-rule').is_displayed()
    assert header_html == '<th>Activity</th><th>Ruleset</th><th>Rule</th><th>Explanation</th><th>Path</th>'
