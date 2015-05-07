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


def test_index_page(server_url, browser):
    browser.get(server_url + '/ocds/')
    assert 'Open Contracting Data Tool' in browser.find_element_by_tag_name('body').text
    assert 'How to use the Open Contracting Data Tool' in browser.find_element_by_tag_name('body').text
    assert 'Why provide converted versions?' in browser.find_element_by_tag_name('body').text


def test_accordion(server_url, browser):
    browser.get(server_url + '/ocds/')

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


@pytest.mark.parametrize('source_url', [
    'https://raw.githubusercontent.com/OpenDataServices/flatten-tool/master/flattentool/tests/fixtures/tenders_releases_2_releases.json',
    'https://github.com/OpenDataServices/cove/raw/master/cove/fixtures/tenders_releases_2_releases.xlsx"',
    'https://github.com/OpenDataServices/cove/blob/master/cove/fixtures/tenders_releases_2_releases.xlsx?raw=true',
    ])
def test_URL_input_json(server_url, browser, source_url):
    browser.get(server_url + '/ocds/')
    browser.find_element_by_partial_link_text('Link').click()
    time.sleep(0.5)
    browser.find_element_by_id('id_source_url').send_keys(source_url)
    browser.find_element_by_css_selector("#fetchURL > div.form-group > button.btn.btn-primary").click()
    assert 'Download Files' in browser.find_element_by_tag_name('body').text

    # We should still be in the OCDS app
    assert 'Open Contracting Data Tool' in browser.find_element_by_tag_name('body').text
