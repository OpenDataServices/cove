import pytest
from selenium import webdriver

@pytest.fixture(scope="module")
def browser(request):
    browser = webdriver.Firefox()
    browser.implicitly_wait(3)
    request.addfinalizer(lambda: browser.quit())
    return browser


def test_index_page(live_server, browser):
    browser.get(live_server.url + '/')
    assert 'Open Contracting Data Explorer' in browser.find_element_by_tag_name('body').text
