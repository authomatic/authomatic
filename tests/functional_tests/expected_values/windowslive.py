import datetime

import fixtures
import constants
from authomatic.providers import oauth2


conf = fixtures.get_configuration('windowslive')

PICTURE = 'https://apis.live.net/v5.0/{0}/picture'.format(conf.user_id)

CONFIG = {
    'login_xpath': '//*[@id="i0116"]',
    'password_xpath': '//*[@id="i0118"]',
    'consent_xpaths': [
        '//*[@id="idSIButton9"]',
        '//*[@id="btnYes"]',
    ],
    'consent_wait_seconds': 0,
    'class_': oauth2.WindowsLive,
    'scope': oauth2.WindowsLive.user_info_scope,
    'offline': True,
    'user': {
        'birth_date': None,
        'city': None,
        'country': None,
        'email': conf.user_email,
        'first_name': conf.user_first_name,
        'gender': None,
        'id': conf.user_id,
        'last_name': conf.user_last_name,
        'link': 'https://profile.live.com/',
        'locale': conf.user_locale,
        'name': conf.user_name,
        'nickname': None,
        'phone': None,
        'picture': PICTURE,
        'postal_code': None,
        'timezone': None,
        'username': None,
    },
    'content_should_contain': [
        conf.user_email,
        conf.user_first_name,
        conf.user_id,
        conf.user_last_name,
        conf.user_locale,
        conf.user_name,
        'https://profile.live.com/',

        # User info JSON keys
        'id', 'name', 'first_name', 'last_name', 'link', 'gender', 'emails',
        'preferred', 'account', 'personal', 'business', 'locale', 'updated_time'
    ],
    # Case insensitive
    'content_should_not_contain':
        conf.no_birth_date +
        # conf.no_gender + # Gender JSON key is there but is alwas null
        [constants.GENDER_MALE] +
        conf.no_location +
        conf.no_nickname +
        conf.no_phone +
        conf.no_timezone +
        conf.no_username,
    # True means that any thruthy value is expected
    'credentials': {
        'token_type': 'Bearer',
        'provider_type_id': '2-14',
        '_expiration_time': True,
        'consumer_key': None,
        'provider_id': None,
        'consumer_secret': None,
        'token': True,
        'token_secret': None,
        '_expire_in': True,
        'provider_name': 'windowslive',
        'refresh_token': True,
        'provider_type': 'authomatic.providers.oauth2.OAuth2',
        'refresh_status': constants.CREDENTIALS_REFRESH_OK,
    },
    # Testing changes after credentials refresh
    # same: True
    # not same: False
    # don't test: None
    'credentials_refresh_change': {
        'token_type': True,
        'provider_type_id': True,
        '_expiration_time': False,
        'consumer_key': True,
        'provider_id': True,
        'consumer_secret': True,
        'token': False,
        'token_secret': True,
        '_expire_in': True,
        'provider_name': True,
        'refresh_token': False,
        'provider_type': True,
    },
}