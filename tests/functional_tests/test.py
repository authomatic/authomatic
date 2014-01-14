# encoding: utf-8

import os

from selenium import webdriver
from selenium.webdriver.common.keys import Keys
import pytest
import liveandletdie

from tests.functional_tests.config import CONFIG


HOST = '127.0.0.1'
PORT = 8080
HOME = 'http://authomatic.com:{}/'.format(PORT)

PROJECT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '../..'))
EXAMPLES_DIR = os.path.join(PROJECT_DIR, 'examples')


APPS = {
    'Flask': liveandletdie.Flask(os.path.join(EXAMPLES_DIR,
                                              'flask/functional_test/main.py'),
                                 suppress_output=False,
                                 host=HOST,
                                 port=PORT),
}


@pytest.fixture('module')
def browser(request):
    """Starts and stops the server for each app in APPS"""

    browser = webdriver.Chrome()
    browser.implicitly_wait(3)
    request.addfinalizer(lambda: browser.quit())
    return browser


@pytest.fixture('module', APPS)
def app(request):
    """Starts and stops the server for each app in APPS"""

    _app = APPS[request.param]
    _app.name = request.param

    try:
        # Run the live server.
        _app.live(kill=True)
    except Exception as e:
        # Skip test if not started.
        pytest.fail(e.message)

    request.addfinalizer(lambda: _app.die())
    return _app


@pytest.fixture(scope='module', params=CONFIG)
def provider(request, browser):
    """Runs for each provider."""

    print 'PROVIDER {}'.format(request.param)

    _provider = CONFIG[request.param]
    _provider['name'] = request.param
    provider_fixture = _provider['fixture']

    # Andy types the login handler url to the address bar.
    browser.get(HOME + 'login/' + _provider['name'])

    # Andy authenticates by the provider.
    provider_fixture.login_function(browser)

    # Andy authorizes this app to access his protected resources.
    provider_fixture.consent_function(browser)

    return _provider


class TestUser(object):
    @pytest.fixture()
    def user_property(self, app, provider, browser):
        def f(property_name):
            value = browser.find_element_by_id(property_name).text
            assert value == provider['user'][property_name]
        return f

    def test_name(self, user_property):
        user_property('name')

    def test_id(self, user_property):
        user_property('id')
