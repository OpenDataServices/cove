import pytest
from selenium import webdriver
import time


@pytest.fixture(scope="module")
def browser(request):
    browser = webdriver.Firefox()
    browser.implicitly_wait(3)
    request.addfinalizer(lambda: browser.quit())
    return browser


def test_index_page(live_server, browser):
    browser.get(live_server.url + '/')
    assert 'Open Contracting Data Explorer' in browser.find_element_by_tag_name('body').text


def test_accordion(live_server, browser):
    browser.get(live_server.url + '/')

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
