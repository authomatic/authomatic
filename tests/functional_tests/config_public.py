# -*- coding: utf-8 -*-
import datetime
import os

from pyvirtualdisplay import Display
from selenium import webdriver

import constants


# Choose and configure the browser of your choice
def get_browser():
    # # These work on Mac
    # return webdriver.Chrome()
    # return webdriver.Firefox()

    # On Linux you need to initialize a display
    global display
    display = Display(visible=0, size=(1024, 768))
    display.start()

    options = webdriver.ChromeOptions()
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage");
    options.add_experimental_option("useAutomationExtension", False);
    return webdriver.Chrome(chrome_options=options)


# If present and callable, it will be called at the end of the whole test suite
def teardown():
    global display
    try:
        display.stop()
    except NameError:
        pass


# A failed login by a provider will be retried so many times as set here
MAX_LOGIN_ATTEMPTS = 3
# Multiplies the wait times set in expected values
WAIT_MULTIPLIER = 1
# Minimum wait time
MIN_WAIT = 0

# The host and port where the tested ap should listen.
HOST = '127.0.0.1'
PORT = 443

# The host alias set in the /etc/hosts file.
# The actual tests will navigate selenium browser to this host.
# This is necessary because some providers don't support localhost as the
# callback url.
HOST_ALIAS = 'authomatic.org'

# Only frameworks included here will be tested.
INCLUDE_FRAMEWORKS = [
    # 'django',
    'flask',  # Runs with https
    # 'pyramid',
]

# Only providers included here will be tested.
# Leave commented-out entries (with explanation) to prevent trying to re-add tests for services
# Which aren't testable in an automated environment.
INCLUDE_PROVIDERS = [
    # OAuth 1.0a  - This mostly deprecated as a service 'in the wild' - we should drop support.
    # 'bitbucket',
    # 'flickr',
    # 'plurk',
     'twitter',
    # 'tumblr',
    # 'ubuntuone',  # UbuntuOne service is no longer available
    # 'vimeo',
    # Xero requires creation of a new trial project every month which makes
    # the setup of the automated test too laborious to support it.
    # 'xero',
    # 'xing',
    # 'yahoo',

    # OAuth 2.0
    # 'amazon',  # Asks for a captcha (cannot be automated)
    # 'behance',  # doesn't support third party authorization anymore.
    # 'bitly',  # deprecated for test suite refactoring - consider re-enabling
    # 'deviantart',  # deprecated for test suite refactoring - consider re-enabling
    'facebook',
    # 'foursquare',  # deprecated for test suite refactoring - consider re-enabling
    # 'google',  # deprecated for test suite refactoring - consider re-enabling
    # 'github', # Asks for 2FA/one-time-pass verification in Travis CI environment.
    # 'linkedin',  #  # Asks for verification (captcha) in the login form in Travis CI environment.
    # 'paypal',  # deprecated for test suite refactoring - consider re-enabling
    # 'reddit',  # deprecated for test suite refactoring - consider re-enabling
    # 'vk',  # deprecated for test suite refactoring - consider re-enabling
    # 'windowslive',  # Asks for verification (captcha) in the login form in Travis CI environment.
    # 'yammer',  # deprecated for test suite refactoring - consider re-enabling
    # 'yandex',  # deprecated for test suite refactoring - consider re-enabling

    # OpenID
    # 'openid_livejournal',  # Login and password elements are not visible.
    # 'openid_verisignlabs',  # deprecated for test suite refactoring - consider re-enabling
    # 'openid_wordpress',  # deprecated for test suite refactoring - consider re-enabling
    # 'openid_yahoo',  # deprecated for test suite refactoring - consider re-enabling
]

# Recommended setup for Travis CI environment.
if os.environ.get('TRAVIS'):
    MAX_LOGIN_ATTEMPTS = 20
    WAIT_MULTIPLIER = 2
    MIN_WAIT = 2


# Use these constants if you have the same user info by all tested providers.
EMAIL = 'authomaticproject@protonmail.com'
FIRST_NAME = 'Authomatic'
LAST_NAME = 'Testuser'
NAME = FIRST_NAME + ' ' + LAST_NAME
USERNAME = 'authomaticproject'
USERNAME_REVERSE = 'projectauthomatic'
NICKNAME = 'Mr. AP'
BIRTH_YEAR = 2000
BIRTH_MONTH = 5
BIRTH_DAY = 5
BIRTH_DATE = datetime.datetime(BIRTH_YEAR, BIRTH_MONTH, BIRTH_DAY)
CITY = 'London'
COUNTRY = 'Great Britain'
COUNTRY_ISO2 = 'gb'
POSTAL_CODE = 'EC1A1DH'
PHONE = '??????????'
PHONE_INTERNATIONAL = '0044??????????'
GENDER = constants.GENDER_MALE
LOCALE = 'en_UK'
LOCATION = CITY + ', ' + COUNTRY

# Common values for all providers
COMMON = {
    # Could be same if the user sets it so
    'user_birth_date': BIRTH_DATE,
    'user_birth_day': BIRTH_DAY,
    'user_birth_month': BIRTH_MONTH,
    'user_birth_year': BIRTH_YEAR,
    'user_login': EMAIL,
    'user_email': EMAIL,
    'user_first_name': FIRST_NAME,
    'user_last_name': LAST_NAME,
    'user_name': NAME,
    'user_username': USERNAME,
    'user_username_reverse': USERNAME_REVERSE,
    'user_nickname': NICKNAME,
    'user_birth_year': BIRTH_YEAR,
    'user_city': CITY,
    'user_country': COUNTRY,
    'user_gender': GENDER,
    'user_phone': PHONE,
    'user_postal_code': POSTAL_CODE,
    'user_locale': LOCALE,
    'user_location': LOCATION,

    # It is not a good idea to have the same password for all providers
    # 'user_password': '##########',

    # Provider and user specific value
    # 'user_id': '',
    # 'user_locale': None,
    # 'user_timezone': None,

    # Provider specific format
    # 'user_picture': '',
    # 'user_link': '',

    # Provider specific value
    # 'consumer_key': '',
    # 'consumer_secret': '',
}

# Values from COMMON will be overridden by values from PROVIDERS[provider_name]
# if set.
# Since this file is public, only put providers in here if they aren't secret.
# Otherwise, secret providers should be added to config_secret.py[.enc]
PROVIDERS = {
#     # OAuth 2.0
#     'facebook': {
#         'consumer_key': '##########',
#         'consumer_secret': '##########',
#         'user_password': '##########',
#         'user_id': '??????????',
#     },
}
