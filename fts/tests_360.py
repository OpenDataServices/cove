import pytest
import requests
from selenium import webdriver
import time
import os

BROWSER = os.environ.get('BROWSER', 'Firefox')


@pytest.fixture(scope="module")
def browser(request):
    browser = getattr(webdriver, BROWSER)()
    browser.implicitly_wait(3)
    request.addfinalizer(lambda: browser.quit())
    return browser


@pytest.fixture(scope="module")
def server_url_360(request, live_server):
    if 'CUSTOM_SERVER_URL' in os.environ:
        return os.environ['CUSTOM_SERVER_URL'] + '/360/'
    else:
        return live_server.url + '/360/'


@pytest.mark.parametrize(('source_filename', 'expected_text', 'conversion_successful'), [
    ('WellcomeTrust-grants_fixed_2_grants.json', ['A file was downloaded from',
                                                  'This file contains 4 grants from 1 funder to 2 recipients awarded on 24/07/2014',
                                                  'The grants were awarded in GBP with a total value of £662,990',
                                                  'individual awards ranging from £152,505 (lowest) to £178,990 (highest)',
                                                  'Convert to Spreadsheet',
                                                  'Invalid against Schema 17 Errors',
                                                  'There are some validation errors in your data, please check them in the table below',
                                                  'Value is not a string',
                                                  'Non-unique ID Values (first 3 shown)',
                                                  'Grant identifiers:  2 IDs',
                                                  'Funder organisation identifiers:  1 ID',
                                                  '360G-wellcometrust-105182/Z/14/Z'], True),
    ('WellcomeTrust-grants_broken_grants.json', ['Invalid against Schema 18 Errors',
                                                 'Value is not a integer',
                                                 'Review 4 Grants',
                                                 'Funder organisation identifiers:  2 IDs',
                                                 'Recipient organisation identifiers:  2 IDs',
                                                 '360G-wellcometrust-105177/Z/14/Z'], True),
    ('WellcomeTrust-grants_2_grants.xlsx', ['This file contains 2 grants from 1 funder to 1 recipient',
                                            'The grants were awarded in GBP with a total value of £331,495',
                                            'Converted to JSON',
                                            'If there are conversion errors, the data may not look as you expect',
                                            'Invalid against Schema 7 Errors',
                                            '\'description\' is missing but required',
                                            'Sheet: grants Row: 2',
                                            'Review 2 Grants',
                                            'Funder organisation identifiers:  1 ID',
                                            'Recipient organisation identifiers:  1 ID',
                                            '360G-wellcometrust-105177/Z/14/Z'], True),
    # Test conversion warnings are shown
    ('tenders_releases_2_releases.xlsx', ['Converted to JSON 5 Warnings',
                                          'Invalid against Schema 76 Errors',
                                          'Conflict when merging field "ocid" for id "1" in sheet items'], True),
    # Test that titles that aren't in the rollup are converted correctly
    # (See @check_url_input_result_page).
    ('WellcomeTrust-grants_2_grants_titleswithoutrollup.xlsx', [], True),
    # Test a 360 csv in cp1252 encoding
    ('WellcomeTrust-grants_2_grants_cp1252.csv', ['This file contains 2 grants from 1 funder to 1 recipient',
                                                  'The grants were awarded in GBP with a total value of £331,495',
                                                  'This file is not \'utf-8\' encoded (it is cp1252 encoded)'], True),
    # Test a non-valid file.
    ('paul-hamlyn-foundation-grants_dc.txt', 'We can only process json, csv and xlsx files', False),
    # Test a unconvertable spreadsheet (blank file)
    ('bad.xlsx', 'We think you tried to supply a spreadsheet, but we failed to convert it to JSON.', False),
])
def test_explore_360_url_input(server_url_360, browser, httpserver, source_filename, expected_text, conversion_successful):
    """
    TODO Test sequence: uploading JSON, files to Download only original, click convert,
    new http request, 'Data Supplied' collapse. 'Download and Share' uncollapsed,
    converted files added.

    TODO Test file with grants in different currencies, check right text in 'Data Supplied'

    TODO Test file with grants awarded on different dates, check right text in 'Data Supplied'
    """
    with open(os.path.join('cove', 'fixtures', source_filename), 'rb') as fp:
        httpserver.serve_content(fp.read())
    if 'CUSTOM_SERVER_URL' in os.environ:
        # Use urls pointing to GitHub if we have a custom (probably non local) server URL
        source_url = 'https://raw.githubusercontent.com/OpenDataServices/cove/master/cove/fixtures/' + source_filename
    else:
        source_url = httpserver.url + '/360/' + source_filename

    browser.get(server_url_360)
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

    # Do the assertions
    check_url_input_result_page(server_url_360, browser, httpserver, source_filename, expected_text, conversion_successful)


def check_url_input_result_page(server_url_360, browser, httpserver, source_filename, expected_text, conversion_successful):
    body_text = browser.find_element_by_tag_name('body').text
    if isinstance(expected_text, str):
        expected_text = [expected_text]

    for text in expected_text:
        assert text in body_text

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
        assert '0 bytes' not in body_text
        # Test for Load New File button
        assert 'Load New File' in body_text

        original_file_response = requests.get(original_file)
        assert original_file_response.status_code == 200
        assert int(original_file_response.headers['content-length']) != 0

        if source_filename.endswith('.xlsx') or source_filename.endswith('.csv'):
            converted_file_response = requests.get(converted_file)
            if source_filename == 'WellcomeTrust-grants_2_grants_titleswithoutrollup.xlsx':
                grant1 = converted_file_response.json()['grants'][1]
                assert grant1['recipientOrganization'][0]['department'] == 'Test data'
                assert grant1['classifications'][0]['title'] == 'Test'
            assert converted_file_response.status_code == 200
            assert int(converted_file_response.headers['content-length']) != 0
