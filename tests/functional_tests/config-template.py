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
    return webdriver.Firefox()


# If present and callable, it will be called at the end of the whole test suite
def teardown():
    global display
    display.stop()


# A failed login by a provider will be retried so many times as set here
MAX_LOGIN_ATTEMPTS = 3
# Multiplies the wait times set in expected values
WAIT_MULTIPLIER = 1
# Minimum wait time
MIN_WAIT = 0

# The host and port where the tested ap shoud listen.
HOST = '127.0.0.1'
PORT = 80

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
INCLUDE_PROVIDERS = [
    # OAuth 1.0a
    'bitbucket',
    'flickr',
    'plurk',
    'twitter',
    'tumblr',
    # 'ubuntuone',  # UbuntuOne service is no longer available
    'vimeo',
    'xero',
    'xing',
    'yahoo',

    # OAuth 2.0
    'amazon',
    # 'behance',  # doesn't support third party authorization anymore.
    'bitly',
    'deviantart',
    'facebook',
    'foursquare',
    'google',
    'github',
    'linkedin',
    'paypal',
    'reddit',
    'vk',
    'windowslive',
    'yammer',
    'yandex',

    # OpenID
    'openid_livejournal',
    'openid_verisignlabs',
    'openid_wordpress',
    'openid_yahoo',
]

# Recommended setup for Travis CI environment.
if os.environ.get('TRAVIS'):
    MAX_LOGIN_ATTEMPTS = 20
    WAIT_MULTIPLIER = 2
    MIN_WAIT = 2

    # LinkedIn and WindowsLive include a captcha in the login form
    # if a user logs in from an unusual location.
    INCLUDE_PROVIDERS = list(set(INCLUDE_PROVIDERS) -
                             set(['linkedin', 'windowslive']))

    def get_browser():
        # Eventbrite has problems with the login form on Firefox
        return webdriver.Chrome()

    def teardown():
        pass

# Use these constants if you have the same user info by all tested providers.
EMAIL = 'andy.pipkin@littlebritain.co.uk'
FIRST_NAME = 'Andy'
LAST_NAME = 'Pipkin'
NAME = FIRST_NAME + ' ' + LAST_NAME
USERNAME = 'andypipkin'
USERNAME_REVERSE = 'pipkinandy'
NICKNAME = 'Mr. Pipkin'
BIRTH_YEAR = '1979'
BIRTH_DATE = datetime.datetime(1979, 12, 31).strftime('%x')
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

# Values from COMMON will be overriden by values from PROVIDERS[provider_name]
# if set.
PROVIDERS = {
    # OAuth 1.0a
    'bitbucket': {
        'consumer_key': '##########',
        'consumer_secret': '##########',
        'user_password': '##########',
        'user_id': USERNAME,
    },
    'flickr': {
        'consumer_key': '##########',
        'consumer_secret': '##########',
        'user_password': '##########',
        'user_id': '??????????',
    },
    'meetup': {
        'consumer_key': '##########',
        'consumer_secret': '##########',
        'user_password': '##########',
        'user_login': EMAIL,
        'user_id': '??????????',
        'user_country': COUNTRY_ISO2,
        'user_location': '{0}, {1}'.format(CITY, COUNTRY_ISO2),
    },
    'plurk': {
        'consumer_key': '##########',
        'consumer_secret': '##########',
        'user_password': '##########',
        'user_id': '??????????',
    },
    'twitter': {
        'consumer_key': '##########',
        'consumer_secret': '##########',
        'user_password': '##########',
        'user_id': '??????????',
        # Twitter considers selenium login attempts suspicious and occasionally
        # asks a security challenge question. This will be used as the answer.
        'user_challenge_answer': '??????????',
    },
    'tumblr': {
        'consumer_key': '##########',
        'consumer_secret': '##########',
        'user_password': '##########',
        'user_id': USERNAME,
    },
    'vimeo': {
        'consumer_key': '##########',
        'consumer_secret': '##########',
        'user_password': '##########',
        'user_id': '??????????',
    },
    'xero': {
        'consumer_key': '##########',
        'consumer_secret': '##########',
        'user_password': '##########',
    },
    'xing': {
        'consumer_key': '##########',
        'consumer_secret': '##########',
        'user_password': '##########',
        'user_id': '??????????',
    },
    'yahoo': {
        'consumer_key': '##########',
        'consumer_secret': '##########',
        'user_password': '##########',
    },

    # OAuth 2.0
    'amazon': {
        'consumer_key': '##########',
        'consumer_secret': '##########',
        'user_id': '??????????',
        'user_password': '##########',
    },
    # Behance doesn't support third party authorization anymore.
    # 'behance': {
    #     'consumer_key': '##########',
    #     'consumer_secret': '##########',
    #     'user_password': '##########',
    #     'user_id': '??????????',
    # },
    'bitly': {
        'consumer_key': '##########',
        'consumer_secret': '##########',
        'user_password': '##########',
        'user_id': '??????????',
    },
    'deviantart': {
        'consumer_key': '##########',
        'consumer_secret': '##########',
        'user_password': '##########',
    },
    'eventbrite': {
        'consumer_key': '##########',
        'consumer_secret': '##########',
        'user_password': '##########',
        'user_id': '??????????',
    },
    'facebook': {
        'consumer_key': '##########',
        'consumer_secret': '##########',
        'user_password': '##########',
        'user_id': '??????????',
    },
    'foursquare': {
        'consumer_key': '##########',
        'consumer_secret': '##########',
        'user_password': '##########',
        'user_id': '??????????',
    },
    'google': {
        'consumer_key': '##########',
        'consumer_secret': '##########',
        'user_password': '##########',
        'user_id': '??????????',
    },
    'github': {
        'consumer_key': '##########',
        'consumer_secret': '##########',
        'user_password': '##########',
        'user_id': '??????????',
    },
    'linkedin': {
        'consumer_key': '##########',
        'consumer_secret': '##########',
        'user_password': '##########',
        'user_id': '??????????',
    },
    'paypal': {
        'consumer_key': '##########',
        'consumer_secret': '##########',
    },
    'reddit': {
        'consumer_key': '##########',
        'consumer_secret': '##########',
        'user_id': '??????????',
    },
    # Viadeo doesn't support access to its API
    # http://dev.viadeo.com/documentation/authentication/request-an-api-key/
    # 'viadeo': {
    #     'consumer_key': '##########',
    #     'consumer_secret': '##########',
    # },
    'vk': {
        'consumer_key': '##########',
        'consumer_secret': '##########',
        'user_password': '##########',
        'user_id': '??????????',
    },
    'windowslive': {
        'consumer_key': '##########',
        'consumer_secret': '##########',
        'user_password': '##########',
        'user_id': '??????????',
    },
    'yammer': {
        'consumer_key': '##########',
        'consumer_secret': '##########',
        'user_password': '##########',
        'user_id': '??????????',
        'user_timezone': '??????????',  # e.g. 'Pacific Time (US & Canada)'
    },
    'yandex': {
        'consumer_key': '##########',
        'consumer_secret': '##########',
        'user_password': '##########',
        'user_id': '??????????',
    },

    # OpenID
    'openid_livejournal': {
        'user_login': USERNAME,
        'user_password': '##########',
    },
    'openid_wordpress': {
        'user_login': EMAIL,
        # user_username is used in the OpenID identifier
        'user_password': '##########',
    },
    'openid_verisignlabs': {
        'user_login': USERNAME,
        'user_password': '##########',
    },
    'openid_yahoo': {
        'user_id': 'https://me.yahoo.com/a/???',
        'user_login': USERNAME,
        'user_password': '##########',
    },
}
