# encoding: utf-8

import os

from selenium import webdriver
from selenium.webdriver.common.keys import Keys
import pytest
import liveandletdie

from tests.functional_tests.config import CONFIG


HOST = '127.0.0.1:8080'
HOME = 'authomatic-functional-test.com:8080'
PROJECT_DIR = path.abspath(path.join(path.dirname(__file__), '../..', pth))
EXAMPLES_PATH = testliveserver.abspath(__file__, '../../examples')
LIVESERVER_PATH = testliveserver.abspath(__file__, '../../examples/flask/functional_test/main.py')



APPS = {
    'Flask': liveandletdie.Flask(abspath('sample_apps/flask/main.py'),
                                 port=PORT),
}


@pytest.fixture(scope='module', params=CONFIG)
def provider(request):
    '''Runs for each provider.'''

    provider = CONFIG[request.param]
    provider['name'] = request.param
    return provider


@pytest.fixture(scope='module', params=APPS)
def app(request):
    '''Runs for each app.'''

    process = None
    app_path = os.path.join(EXAMPLES_PATH, request.param)
    try:
        # Run the live server.
        process = testliveserver.start(app_path, HOST)
    except Exception as e:
        # Stop all tests if not started.
        pytest.exit(format(e.message))

    # Start the browser.
    browser = webdriver.Chrome()
    browser.implicitly_wait(3)

    def fin():
        if hasattr(process, 'terminate'):
            process.terminate()

        # Stop the browser.
        if hasattr(browser, 'quit'):
            pass
            browser.quit()

    request.addfinalizer(fin)

    result = lambda: None
    result.browser = browser

    return result


@pytest.fixture(scope='module')
def world(app, provider):
    '''Redirects the user to a login handler, logs him in by the provider and clicks all consent buttons.'''
    
    # Andy types the login handler url to the address bar.
    app.browser.get(HOME + '/login/' + provider.get('name'))
    
    # Andy authenticates by the provider.
    provider.get('login_funct')(app.browser)
    
    # Andy authorizes this app to access his protected resources.
    provider.get('consent_funct')(app.browser)
    
    app.user = provider.get('user')    
    return app


def test_user_name(world):
    """User sees his name."""
    
    value = world.browser.find_element_by_id('name').text
    assert value == world.user.get('name')


def test_user_id(world):
    """User sees his name."""

    value = world.browser.find_element_by_id('id').text
    assert value == world.user.get('id')
    
    





