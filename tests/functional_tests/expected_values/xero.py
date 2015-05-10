import fixtures
import constants
from authomatic.providers import oauth1

conf = fixtures.get_configuration('xero')

CONFIG = {
    'login_xpath': '//*[@id="email"]',
    'password_xpath': '//*[@id="password"]',
    'consent_xpaths': [
        '//*[@id="SelectedOrganisation_toggle"]',
        '//*[@id="SelectedOrganisation_suggestions"]/div/div',
        '//*[@id="ext-gen4"]'
    ],
    'consent_wait_seconds': 1,
    'after_consent_wait_seconds': 3,
    'class_': oauth1.Xero,
    'user': {
        'birth_date': None,
        'city': None,
        'country': None,
        'email': conf.user_email,
        'gender': None,
        'id': conf.user_id,
        'first_name': conf.user_first_name,
        'last_name': conf.user_last_name,
        'link': None,
        'locale': None,
        'location': None,
        'name': conf.user_name,
        'nickname': None,
        'phone': None,
        'picture': None,
        'postal_code': None,
        'timezone': None,
        'username': None,
    },
    'content_should_contain': [
        conf.user_email,
        conf.user_first_name,
        conf.user_id,
        conf.user_last_name,
        conf.user_name,

        # User info JSON keys
    ],
    # Case insensitive
    'content_should_not_contain':
        conf.no_birth_date +
        conf.no_gender +
        conf.no_link +
        conf.no_locale +
        conf.no_location +
        conf.no_nickname +
        conf.no_phone +
        conf.no_picture +
        conf.no_timezone +
        conf.no_username,
    # True means that any thruthy value is expected
    'credentials': {
        '_expiration_time': None,
        '_expire_in': True,
        'consumer_key': True,
        'consumer_secret': True,
        'provider_id': None,
        'provider_name': 'xero',
        'provider_type': 'authomatic.providers.oauth1.OAuth1',
        'provider_type_id': '1-9',
        'refresh_status': constants.CREDENTIALS_REFRESH_NOT_SUPPORTED,
        'refresh_token': None,
        'token': True,
        'token_secret': True,
        'token_type': None,
    },
}