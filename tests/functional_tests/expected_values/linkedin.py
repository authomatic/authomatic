import fixtures
import constants
from authomatic.providers import oauth2


conf = fixtures.get_configuration('linkedin')


CONFIG = {
    'login_xpath': '//*[@id="session_key-oauth2SAuthorizeForm"]',
    'password_xpath': '//*[@id="session_password-oauth2SAuthorizeForm"]',
    'consent_xpaths': [
        '//*[@id="body"]/div/form/div[2]/ul/li[1]/input',
    ],
    'class_': oauth2.LinkedIn,
    'scope': oauth2.LinkedIn.user_info_scope,
    'user': {
        'birth_date': conf.user_birth_date,
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
        'phone': conf.user_phone,
        'picture': conf.user_picture,
        'postal_code': None,
        'timezone': None,
        'username': None,
    },
    'content_should_contain': [
        conf.user_id,
        conf.user_name, conf.user_first_name, conf.user_last_name,
        conf.user_country,
        conf.user_email,
        conf.user_link,
        conf.user_phone,
        conf.user_picture,

        # User info JSON keys
        'dateOfBirth', 'day', 'month', 'year', 'emailAddress', 'firstName',
        'formattedName', 'id', 'lastName', 'location', 'country', 'code',
        'name', 'phoneNumbers', '_total', 'values', 'phoneNumber', 'phoneType',
        'pictureUrl', 'publicProfileUrl',
    ],
    # Case insensitive
    'content_should_not_contain':
        conf.no_timezone +
        conf.no_postal_code +
        conf.no_locale +
        conf.no_gender +
        conf.no_city +
        [
            conf.user_nickname,
            '"{0}"'.format(conf.user_username),
            '"{0}"'.format(conf.user_username_reverse),
        ],
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