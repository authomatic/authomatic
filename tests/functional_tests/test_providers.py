# encoding: utf-8

import os
import time

from selenium import webdriver
from selenium.webdriver.common.keys import Keys
import pytest
import liveandletdie

from tests.functional_tests import config
from tests.functional_tests import fixtures
import constants


HOME = 'http://{0}:{1}/'.format(config.HOST_ALIAS, config.PORT)
PROJECT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '../..'))
EXAMPLES_DIR = os.path.join(PROJECT_DIR, 'examples')
PROVIDERS = dict((k, v) for k, v in fixtures.ASSEMBLED_CONFIG.items() if
                 k in config.INCLUDE_PROVIDERS)
APPS = {
    'Flask': liveandletdie.Flask(
        os.path.join(EXAMPLES_DIR, 'flask/functional_test/main.py'),
        suppress_output=False,
        host=config.HOST,
        port=config.PORT
    ),
}


@pytest.fixture('module')
def browser(request):
    """Starts and stops the server for each app in APPS"""

    _browser = webdriver.Chrome()
    _browser.implicitly_wait(3)
    request.addfinalizer(lambda: _browser.quit())
    return _browser


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


def user_consent(browser, xpath):
    try:
        button = browser.find_element_by_xpath(xpath)
        print('Hitting consent button.')
        button.click()
    except Exception as e:
        print('No consent needed.')
        pass


@pytest.fixture(scope='module', params=PROVIDERS)
def provider(request, browser):
    """Runs for each provider."""

    _provider = fixtures.ASSEMBLED_CONFIG[request.param]
    _provider['name'] = request.param
    conf = fixtures.get_configuration(request.param)

    # Andy types the login handler url to the address bar.
    browser.get(HOME + 'login/' + _provider['name'])

    # Andy authenticates by the provider.
    login_xpath = _provider.get('login_xpath')
    password_xpath = _provider.get('password_xpath')
    pre_login_xpaths = _provider.get('pre_login_xpaths')
    if login_xpath:
        if pre_login_xpaths:
            for xpath in pre_login_xpaths:
                print('clicking on {0}'.format(xpath))
                browser.find_element_by_xpath(xpath).click()

        print('logging the user in.')
        browser.find_element_by_xpath(login_xpath)\
            .send_keys(conf.user_login)
        password_element = browser.\
            find_element_by_xpath(password_xpath)
        password_element.send_keys(conf.user_password)
        password_element.send_keys(Keys.ENTER)

    # Andy authorizes this app to access his protected resources.
    consent_xpaths = _provider.get('consent_xpaths')
    consent_wait_seconds = _provider.get('consent_wait_seconds', 0)
    if consent_xpaths:
        for xpath in consent_xpaths:
            try:
                time.sleep(consent_wait_seconds)
                button = browser.find_element_by_xpath(xpath)
                print('Hitting consent button.')
                button.click()
            except Exception as e:
                print('No consent needed.')
                pass

    return _provider


class TestCredentials(object):

    @pytest.fixture()
    def fixture(self, app, provider, browser):
        def f(property_name):
            id_ = 'original-credentials-{0}'.format(property_name)
            value = browser.find_element_by_id(id_).text or None

            expected = provider['credentials'][property_name]
            if expected is True:
                assert value
            else:
                assert value == expected
        return f

    def test_refresh_response(self, fixture):
        # status = browser.find_element_by_id('refresh-status').text
        # assert status == '200'
        fixture('refresh_status')

    def test_token_type(self, fixture):
        fixture('token_type')

    def test_provider_type_id(self, fixture):
        fixture('provider_type_id')

    def test__expiration_time(self, fixture):
        fixture('_expiration_time')

    def test_consumer_key(self, fixture):
        fixture('consumer_key')

    def test_provider_id(self, fixture):
        fixture('provider_id')

    def test_consumer_secret(self, fixture):
        fixture('consumer_secret')

    def test_token(self, fixture):
        fixture('token')

    def test_token_secret(self, fixture):
        fixture('token_secret')

    def test__expire_in(self, fixture):
        fixture('_expire_in')

    def test_provider_name(self, fixture):
        fixture('provider_name')

    def test_refresh_token(self, fixture):
        fixture('refresh_token')

    def test_provider_type(self, fixture):
        fixture('provider_type')


class TestCredentialsChange(object):
    @pytest.fixture()
    def fixture(self, app, provider, browser):
        refresh_status = browser.find_element_by_id('original-credentials-'
                                                      'refresh_status').text

        supports_refresh = refresh_status != \
                           constants.CREDENTIALS_REFRESH_NOT_SUPPORTED

        def f(property_name):
            if not supports_refresh:
                pytest.skip("Doesn't support credentials refresh.")

            changed_values = provider.get('credentials_refresh_change')
            if not changed_values:
                pytest.skip("Credentials refresh values not specified.")
            else:
                original_id = 'original-credentials-{0}'.format(property_name)
                changed_id = 'refreshed-credentials-{0}'.format(property_name)

                original_val = browser.find_element_by_id(original_id).text or \
                               None
                changed_val = browser.find_element_by_id(changed_id).text or \
                              None

                expected = changed_values[property_name]
                if expected is not None:
                    assert (original_val == changed_val) is expected

        return f

    def test_token_type(self, fixture):
        fixture('token_type')

    def test_provider_type_id(self, fixture):
        fixture('provider_type_id')

    def test__expiration_time(self, fixture):
        fixture('_expiration_time')

    def test_consumer_key(self, fixture):
        fixture('consumer_key')

    def test_provider_id(self, fixture):
        fixture('provider_id')

    def test_consumer_secret(self, fixture):
        fixture('consumer_secret')

    def test_token(self, fixture):
        fixture('token')

    def test_token_secret(self, fixture):
        fixture('token_secret')

    def test__expire_in(self, fixture):
        fixture('_expire_in')

    def test_provider_name(self, fixture):
        fixture('provider_name')

    def test_refresh_token(self, fixture):
        fixture('refresh_token')

    def test_provider_type(self, fixture):
        fixture('provider_type')


class TestUser(object):
    @pytest.fixture()
    def fixture(self, app, provider, browser):
        def f(property_name):
            value = browser.find_element_by_id(property_name).text or None
            assert value == provider['user'][property_name]
        return f

    def test_id(self, fixture):
        fixture('id')

    def test_email(self, fixture):
        fixture('email')

    def test_username(self, fixture):
        fixture('username')

    def test_name(self, fixture):
        fixture('name')

    def test_first_name(self, fixture):
        fixture('first_name')

    def test_last_name(self, fixture):
        fixture('last_name')

    def test_nickname(self, fixture):
        fixture('nickname')

    def test_birth_date(self, fixture):
        fixture('birth_date')

    def test_city(self, fixture):
        fixture('city')

    def test_country(self, fixture):
        fixture('country')

    def test_gender(self, fixture):
        fixture('gender')

    def test_link(self, fixture):
        fixture('link')

    def test_locale(self, fixture):
        fixture('locale')

    def test_phone(self, fixture):
        fixture('phone')

    def test_picture(self, fixture):
        fixture('picture')

    def test_postal_code(self, fixture):
        fixture('postal_code')

    def test_timezone(self, fixture):
        fixture('timezone')

    def test_content_should_contain(self, app, provider, browser):
        content = browser.find_element_by_id('content').text
        for item in provider['content_should_contain']:
            assert item in content

    def test_content_should_not_contain(self, app, provider, browser):
        content = browser.find_element_by_id('content').text.lower()
        for item in provider['content_should_not_contain']:
            if item:
                assert item.lower() not in content

    def test_provider_support(self, app, provider):
        sua = provider['class_'].supported_user_attributes
        tested = dict((k, getattr(sua, k)) for k in sua._fields)
        expected = dict((k, bool(v)) for k, v in provider['user'].items() if
                        k is not 'content')
        assert tested == expected
