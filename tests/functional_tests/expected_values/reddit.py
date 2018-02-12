# -*- coding: utf-8 -*-
import fixtures
import constants
from authomatic.providers import oauth2

conf = fixtures.get_configuration('reddit')

CONFIG = {
    'login_xpath': '//*[@id="user_login"]',
    'password_xpath': '//*[@id="passwd_login"]',
    'consent_xpaths': [
        '/html/body/div[3]/div/div[2]/form/div/input[1]',
    ],
    'consent_wait_seconds': 3,
    'class_': oauth2.Reddit,
    'scope': oauth2.Reddit.user_info_scope,
    'access_headers': {
        'User-Agent': ('Authomatic.py Automated Functional Tests'),
    },
    'user': {
        'id': conf.user_id,
        'email': None,
        'username': conf.user_username,
        'name': conf.user_username,
        'first_name': None,
        'last_name': None,
        'nickname': None,
        'birth_date': None,
        'city': None,
        'country': None,
        'gender': None,
        'link': None,
        'locale': None,
        'location': None,
        'phone': None,
        'picture': None,
        'postal_code': None,
        'timezone': None,
    },
    'content_should_contain': [
        conf.user_id,
        conf.user_username,

        # User info JSON keys
        'name', 'created', 'gold_creddits', 'created_utc', 'link_karma',
        'comment_karma', 'over_18', 'is_gold', 'is_mod', 'has_verified_email',
        'id'
    ],
    # Case insensitive
    'content_should_not_contain':
        conf.no_birth_date +
        conf.no_phone +
        conf.no_birth_date +
        conf.no_gender +
        conf.no_locale +
        conf.no_first_name +
        conf.no_last_name +
        conf.no_timezone +
        conf.no_location +
        [conf.user_email],
    # True means that any thruthy value is expected
    'credentials': {
        'token_type': 'Bearer',
        'provider_type_id': '2-11',
        '_expiration_time': True,
        'consumer_key': None,
        'provider_id': None,
        'consumer_secret': None,
        'token': True,
        'token_secret': None,
        '_expire_in': '3600',
        'provider_name': 'reddit',
        'refresh_token': None,
        'provider_type': 'authomatic.providers.oauth2.OAuth2',
        'refresh_status': constants.CREDENTIALS_REFRESH_NOT_SUPPORTED,
    },
}
