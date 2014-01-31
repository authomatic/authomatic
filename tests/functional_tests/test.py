# encoding: utf-8

import os

from selenium import webdriver
from selenium.webdriver.common.keys import Keys
import pytest
import liveandletdie

from tests.functional_tests import config


HOME = 'http://{}:{}/'.format(config.HOST_ALIAS, config.PORT)

PROJECT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '../..'))
EXAMPLES_DIR = os.path.join(PROJECT_DIR, 'examples')


APPS = {
    'Flask': liveandletdie.Flask(os.path.join(EXAMPLES_DIR,
                                              'flask/functional_test/main.py'),
                                 suppress_output=False,
                                 host=config.HOST,
                                 port=config.PORT),
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


@pytest.fixture(scope='module', params=config.PROVIDERS)
def provider(request, browser):
    """Runs for each provider."""

    print 'PROVIDER {}'.format(request.param)

    _provider = config.PROVIDERS[request.param]
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
            value = browser.find_element_by_id(property_name).text or None
            assert value == provider['user'][property_name]
        return f

    def test_id(self, user_property):
        user_property('id')

    def test_email(self, user_property):
        user_property('email')

    def test_username(self, user_property):
        user_property('username')

    def test_name(self, user_property):
        user_property('name')

    def test_first_name(self, user_property):
        user_property('first_name')

    def test_flast_name(self, user_property):
        user_property('first_name')

    def test_nickname(self, user_property):
        user_property('nickname')

    def test_birth_date(self, user_property):
        user_property('birth_date')

    def test_city(self, user_property):
        user_property('city')

    def test_country(self, user_property):
        user_property('country')

    def test_gender(self, user_property):
        user_property('gender')

    def test_link(self, user_property):
        user_property('link')

    def test_locale(self, user_property):
        user_property('locale')

    def test_phone(self, user_property):
        user_property('phone')

    def test_picture(self, user_property):
        user_property('picture')

    def test_postal_code(self, user_property):
        user_property('postal_code')

    def test_timezone(self, user_property):
        user_property('timezone')

    def test_content_should_contain(self, app, provider, browser):
        content = browser.find_element_by_id('content').text
        for item in provider['content_should_contain']:
            assert item in content

    def test_content_should_not_contain(self, app, provider, browser):
        content = browser.find_element_by_id('content').text.lower()
        for item in provider['content_should_not_contain']:
            assert item.lower() not in content
