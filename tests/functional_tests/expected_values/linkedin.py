import re

import fixtures
import constants
from authomatic.providers import oauth2


conf = fixtures.get_configuration('linkedin')

PICTURE = re.compile(r'^https://media.licdn.com/mpr/mprx/[\w_-]+$')


CONFIG = {
    'login_xpath': '//*[@id="session_key-oauth2SAuthorizeForm"]',
    'password_xpath': '//*[@id="session_password-oauth2SAuthorizeForm"]',
    'consent_xpaths': [
        '//*[@id="body"]/div/form/div[2]/ul/li[1]/input',
    ],
    'class_': oauth2.LinkedIn,
    'scope': oauth2.LinkedIn.user_info_scope,
    'user': {
        'birth_date': None,
        'city': None,
        'country': conf.user_country,
        'email': conf.user_email,
        'first_name': conf.user_first_name,
        'gender': None,
        'id': conf.user_id,
        'last_name': conf.user_last_name,
        'link': conf.user_link,
        'locale': None,
        'location': conf.user_location,
        'name': conf.user_name,
        'nickname': None,
        'phone': None,
        'picture': PICTURE,
        'postal_code': None,
        'timezone': None,
        'username': None,
    },
    'content_should_contain': [
        conf.user_country,
        conf.user_email,
        conf.user_first_name,
        conf.user_id,
        conf.user_last_name,
        conf.user_link,
        conf.user_name,

        # User info JSON keys
        'code', 'country', 'emailAddress', 'firstName', 'formattedName', 'id',
        'lastName', 'location', 'name', 'pictureUrl', 'publicProfileUrl',
    ],
    # Case insensitive
    'content_should_not_contain':
        conf.no_birth_date +
        conf.no_city +
        conf.no_gender +
        conf.no_locale +
        conf.no_nickname +
        conf.no_phone +
        conf.no_postal_code +
        conf.no_timezone +
        conf.no_username,
    # True means that any thruthy value is expected
    'credentials': {
        'token_type': None,
        'provider_type_id': '2-9',
        '_expiration_time': True,
        'consumer_key': None,
        'provider_id': None,
        'consumer_secret': None,
        'token': True,
        'token_secret': None,
        '_expire_in': True,
        'provider_name': 'linkedin',
        'refresh_token': None,
        'provider_type': 'authomatic.providers.oauth2.OAuth2',
        'refresh_status': constants.CREDENTIALS_REFRESH_NOT_SUPPORTED,
    },
}