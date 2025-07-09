import datetime
import re

import fixtures
import constants
from authomatic.providers import oauth2


conf = fixtures.get_configuration('vk')

PICTURE = re.compile(r'http://[A-Za-z0-9]+\.vk\.me/[A-Za-z0-9-/]+\.jpg')

CONFIG = {
    'login_xpath': '//*[@id="box"]/div/input[6]',
    'password_xpath': '//*[@id="box"]/div/input[7]',
    'consent_xpaths': [
        '//*[@id="install_allow"]',
    ],
    'consent_wait_seconds': 4,
    'class_': oauth2.VK,
    'scope': oauth2.VK.user_info_scope,
    'offline': True,
    'user': {
        'birth_date': conf.user_birth_date_str,
        'city': re.compile('\d+'),
        'country': re.compile('\d+'),
        'email': None,
        'first_name': conf.user_first_name,
        'gender': re.compile('\d'),
        'id': conf.user_id,
        'last_name': conf.user_last_name,
        'link': None,
        'locale': None,
        'location': re.compile('\d+, \d+'),
        'name': conf.user_name,
        'nickname': None,
        'phone': None,
        'picture': PICTURE,
        'postal_code': None,
        'timezone': re.compile('\d'),
        'username': None,
    },
    'content_should_contain': [
        conf.user_birth_date.strftime('%d.%m.%Y'),
        conf.user_first_name,
        conf.user_id,
        conf.user_last_name,

        # User info JSON keys
        'response', 'uid', 'first_name', 'last_name', 'sex', 'nickname',
        'bdate', 'city', 'country', 'timezone', 'photo_big'
    ],
    # Case insensitive
    'content_should_not_contain':
        conf.no_email +
        conf.no_locale +
        conf.no_phone +
        conf.no_postal_code +
        conf.no_username +
        ['link', conf.user_nickname],
    # True means that any truthy value is expected
    'credentials': {
        'token_type': None,
        'provider_type_id': '2-13',
        '_expiration_time': None,
        'consumer_key': None,
        'provider_id': None,
        'consumer_secret': None,
        'token': True,
        'token_secret': None,
        '_expire_in': True,
        'provider_name': 'vk',
        'refresh_token': None,
        'provider_type': 'authomatic.providers.oauth2.OAuth2',
        'refresh_status': constants.CREDENTIALS_REFRESH_NOT_SUPPORTED,
    },
}
