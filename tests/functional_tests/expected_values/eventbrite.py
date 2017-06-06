import fixtures
import constants
from authomatic.providers import oauth2

conf = fixtures.get_configuration('eventbrite')

CONFIG = {
    'logout_url': 'https://www.eventbrite.com/logout',
    'login_xpath': '//*[@id="login-email"]',
    'password_xpath': '//*[@id="login-password"]',
    'consent_xpaths': [
        '//*[@id="access_choices_allow"]',
    ],
    'before_login_enter_wait': 2,
    'consent_wait_seconds': 2,
    'class_': oauth2.Eventbrite,
    'scope': oauth2.Eventbrite.user_info_scope,
    'user': {
        'birth_date': None,
        'city': None,
        'country': None,
        'email': conf.user_email,
        'first_name': conf.user_first_name,
        'gender': None,
        'id': conf.user_id,
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
        conf.user_last_name,
        conf.user_name,
        conf.user_id,

        # User info JSON keys
        'emails', 'email', 'verified', 'primary', 'id', 'name', 'first_name',
        'last_name'
    ],
    # Case insensitive
    'content_should_not_contain':
        conf.no_birth_date +
        conf.no_gender +
        conf.no_locale +
        conf.no_location +
        conf.no_nickname +
        conf.no_phone +
        conf.no_timezone
        ,
    # True means that any thruthy value is expected
    'credentials': {
        'token_type': 'Bearer',
        'provider_type_id': '2-17',
        '_expiration_time': None,
        'consumer_key': None,
        'provider_id': None,
        'consumer_secret': None,
        'token': True,
        'token_secret': None,
        '_expire_in': True,
        'provider_name': 'eventbrite',
        'refresh_token': None,
        'provider_type': 'authomatic.providers.oauth2.OAuth2',
        'refresh_status': constants.CREDENTIALS_REFRESH_NOT_SUPPORTED,
    },
}