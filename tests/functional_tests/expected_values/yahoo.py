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
    'consent_xpaths': [
        '//*[@id="xagree"]',
    ],
    'consent_wait_seconds': 3,
    'logout_url': 'https://login.yahoo.com/config/login?logout=1',
    'class_': oauth1.Yahoo,
    'user': {
        'birth_date': conf.user_birth_date_str,
        'city': conf.user_city,
        'country': conf.user_country,
        'email': None,
        'gender': re.compile(r'^\w$'),
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
        '"birthYear":"{0:%Y}",'.format(conf.user_birth_date),
        '"birthdate":"{0:%m/%d}",'.format(conf.user_birth_date),
        conf.user_id,
        LINK,
        conf.user_location,
        conf.user_name,

        # User info JSON keys
        'aboutMe', 'ageCategory', 'birthYear', 'birthdate', 'count', 'created',
        'displayAge', 'gender', 'guid', 'height', 'image', 'imageUrl',
        'isConnected', 'lang', 'location', 'memberSince', 'nickname', 'profile',
        'profileUrl', 'query', 'results', 'size', 'width'
    ],
    # Case insensitive
    'content_should_not_contain':
        ['city', 'country'] +
        conf.no_email +
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
