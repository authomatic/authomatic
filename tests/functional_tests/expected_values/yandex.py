import fixtures
import constants
from authomatic.providers import oauth2

conf = fixtures.get_configuration('yandex')

CONFIG = {
    'login_xpath': '//*[@id="login"]',
    'password_xpath': '//*[@id="passwd"]',
    'consent_xpaths': [
        '/html/body/div[2]/div/div[2]/form/div[4]/div[2]/button',
    ],
    'class_': oauth2.Yandex,
    'scope': oauth2.Yandex.user_info_scope,
    'user': {
        'birth_date': None,
        'city': None,
        'country': None,
        'email': None,
        'first_name': None,
        'gender': None,
        'id': conf.user_id,
        'last_name': None,
        'link': None,
        'locale': None,
        'name': None,
        'nickname': None,
        'phone': None,
        'picture': None,
        'postal_code': None,
        'timezone': None,
        'username': None,
    },
    'content_should_contain': [
        conf.user_id,

        # User info JSON keys
        'id',
    ],
    # Case insensitive
    'content_should_not_contain':
        conf.no_birth_date +
        conf.no_email +
        conf.no_first_name +
        conf.no_gender +
        conf.no_last_name +
        conf.no_locale +
        conf.no_location +
        conf.no_nickname +
        conf.no_phone +
        conf.no_postal_code +
        conf.no_timezone +
        conf.no_username,
    # True means that any thruthy value is expected
    'credentials': {
        'token_type': 'Bearer',
        'provider_type_id': '2-16',
        '_expiration_time': True,
        'consumer_key': None,
        'provider_id': None,
        'consumer_secret': None,
        'token': True,
        'token_secret': None,
        '_expire_in': '31536000',
        'provider_name': 'yandex',
        'refresh_token': None,
        'provider_type': 'authomatic.providers.oauth2.OAuth2',
        'refresh_status': constants.CREDENTIALS_REFRESH_NOT_SUPPORTED,
    },
}