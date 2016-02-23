import re

import fixtures
import constants
from authomatic.providers import oauth1

conf = fixtures.get_configuration('bitbucket')


LINK = 'https://bitbucket.org/api/1.0/users/{0}'.format(conf.user_username)

CONFIG = {
    'logout_url': 'https://bitbucket.org/account/signout/',
    'login_xpath': '//*[@id="js-email-field"]',
    'password_xpath': '//*[@id="js-password-field"]',
    'consent_xpaths': [],
    'class_': oauth1.Bitbucket,
    'user': {
        'birth_date': None,
        'city': None,
        'country': None,
        'email': None,
        'first_name': conf.user_first_name,
        'gender': None,
        'id': conf.user_id,
        'last_name': conf.user_last_name,
        'link': LINK,
        'locale': None,
        'location': None,
        'name': conf.user_name,
        'nickname': None,
        'phone': None,
        'picture': re.compile(r'https://bitbucket\.org/account/\w+/avatar/32/.*'),
        'postal_code': None,
        'timezone': None,
        'username': conf.user_username,
    },
    'content_should_contain': [
        conf.user_first_name,
        conf.user_id,
        conf.user_last_name,
        conf.user_username,
        conf.user_name,

        # User info JSON keys
        'avatar', 'display_name', 'first_name', 'is_staff', 'is_team',
        'last_name', 'repositories', 'resource_uri', 'user', 'username'
    ],
    # Case insensitive
    'content_should_not_contain':
        conf.no_birth_date +
        conf.no_email +
        conf.no_gender +
        conf.no_locale +
        conf.no_location +
        conf.no_nickname +
        conf.no_phone +
        conf.no_timezone,
    # True means that any thruthy value is expected
    'credentials': {
        '_expiration_time': None,
        '_expire_in': True,
        'consumer_key': True,
        'consumer_secret': True,
        'provider_id': None,
        'provider_name': 'bitbucket',
        'provider_type': 'authomatic.providers.oauth1.OAuth1',
        'provider_type_id': '1-1',
        'refresh_status': constants.CREDENTIALS_REFRESH_NOT_SUPPORTED,
        'refresh_token': None,
        'token': True,
        'token_secret': True,
        'token_type': None,
    },
}