# -*- coding: utf-8 -*-
import fixtures
import constants
from authomatic.providers import oauth1

conf = fixtures.get_configuration('flickr')

CONFIG = {
    'login_xpath': '//*[@id="login-username"]',
    'password_xpath': '//*[@id="login-passwd"]',
    'consent_xpaths': [
        '//*[@id="permissions"]/form/div/input[1]',
    ],
    'enter_after_login_input': True,
    'before_password_input_wait': 1,
    'consent_wait_seconds': 1,
    'logout_url': 'https://login.yahoo.com/config/login?logout=1',
    'class_': oauth1.Flickr,
    'user_authorization_params': dict(perms='read'),
    'user': {
        'birth_date': None,
        'city': None,
        'country': None,
        'email': None,
        'gender': None,
        'id': conf.user_id,
        'first_name': None,
        'last_name': None,
        'link': None,
        'locale': None,
        'location': None,
        'name': conf.user_name,
        'nickname': None,
        'phone': None,
        'picture': None,
        'postal_code': None,
        'timezone': None,
        'username': conf.user_username,
    },
    'content_should_contain': [],
    # Case insensitive
    'content_should_not_contain': [],
    # True means that any truthy value is expected
    'credentials': {
        '_expiration_time': None,
        '_expire_in': True,
        'consumer_key': True,
        'consumer_secret': True,
        'provider_id': None,
        'provider_name': 'flickr',
        'provider_type': 'authomatic.providers.oauth1.OAuth1',
        'provider_type_id': '1-2',
        'refresh_status': constants.CREDENTIALS_REFRESH_NOT_SUPPORTED,
        'refresh_token': None,
        'token': True,
        'token_secret': True,
        'token_type': None,
    },
}
