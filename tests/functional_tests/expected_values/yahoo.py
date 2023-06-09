# -*- coding: utf-8 -*-
import re

import fixtures
import constants
from authomatic.providers import oauth1

conf = fixtures.get_configuration('yahoo')

LINK = 'http://profile.yahoo.com/{0}'.format(conf.user_id)
PITURE = re.compile(r'https://\w+.yimg.com/dg/users/\w+==.large.png')


CONFIG = {
    'login_xpath': '//*[@id="login-username"]',
    'password_xpath': '//*[@id="login-passwd"]',
    'enter_after_login_input': True,
    'before_password_input_wait': 1,
    'consent_xpaths': [
        '//*[@id="xagree"]',
    ],
    'consent_wait_seconds': 1,
    'logout_url': 'https://login.yahoo.com/config/login?logout=1',
    'class_': oauth1.Yahoo,
    'user': {
        'birth_date': None,
        'city': conf.user_city,
        'country': conf.user_country,
        'email': None,
        'gender': None,
        'id': conf.user_id,
        'first_name': None,
        'last_name': None,
        'link': LINK,
        'locale': None,
        'location': conf.user_location,
        'name': conf.user_name,
        'nickname': conf.user_name,
        'phone': None,
        'picture': PITURE,
        'postal_code': None,
        'timezone': None,
        'username': None,
    },
    'content_should_contain': [
        conf.user_id,
        LINK,
        conf.user_location,
        conf.user_name,

        # User info JSON keys
        'aboutMe', 'ageCategory', 'birthdate', 'count', 'created', 'guid',
        'height', 'image', 'imageUrl', 'isConnected', 'lang', 'location',
        'memberSince', 'nickname', 'profile', 'profileUrl', 'query', 'results',
        'size', 'width'
    ],
    # Case insensitive
    'content_should_not_contain':
        ['city', 'country'] +
        conf.no_birth_year +
        conf.no_email +
        conf.no_gender +
        conf.no_locale +
        ['first_name', 'last_name', 'firstname', 'lastname'] +
        conf.no_phone +
        conf.no_postal_code +
        conf.no_timezone +
        conf.no_username,
    # True means that any thruthy value is expected
    'credentials': {
        '_expiration_time': None,
        '_expire_in': True,
        'consumer_key': True,
        'consumer_secret': True,
        'provider_id': None,
        'provider_name': 'yahoo',
        'provider_type': 'authomatic.providers.oauth1.OAuth1',
        'provider_type_id': '1-10',
        'refresh_status': constants.CREDENTIALS_REFRESH_NOT_SUPPORTED,
        'refresh_token': None,
        'token': True,
        'token_secret': True,
        'token_type': None,
    },
}
