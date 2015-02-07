import datetime
import re

import fixtures
import constants
from authomatic.providers import oauth2


conf = fixtures.get_configuration('vk')

# BIRTH_DATE = datetime.datetime.strptime(conf.user_birth_date[:10], '%Y-%m-%d')
# FORMATTED_DATE = datetime.datetime.strftime(BIRTH_DATE, '%d.%m.%Y')
PICTURE = re.compile(r'http://[A-Za-z0-9]+\.vk\.me/[A-Za-z0-9-/]+\.jpg')

CONFIG = {
    'login_xpath': '//*[@id="box"]/div/input[5]',
    'password_xpath': '//*[@id="box"]/div/input[6]',
    'consent_xpaths': [
        '//*[@id="install_allow"]',
        '//*[@id="install_allow"]',
    ],
    'consent_wait_seconds': 4,
    'class_': oauth2.VK,
    'scope': oauth2.VK.user_info_scope,
    'offline': True,
    'user': {
        'birth_date': conf.user_birth_date,
        'city': conf.user_city,
        'country': conf.user_country,
        'email': None,
        'first_name': conf.user_first_name,
        'gender': conf.user_gender,
        'id': conf.user_id,
        'last_name': conf.user_last_name,
        'link': None,
        'locale': None,
        'name': conf.user_name,
        'nickname': None,
        'phone': None,
        'picture': PICTURE,
        'postal_code': None,
        'timezone': conf.user_timezone,
        'username': None,
    },
    'content_should_contain': [
        # FORMATTED_DATE,
        conf.user_city,
        conf.user_country,
        conf.user_first_name,
        conf.user_gender,
        conf.user_id,
        conf.user_last_name,
        conf.user_timezone,

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
    # True means that any thruthy value is expected
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