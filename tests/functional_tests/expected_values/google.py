import fixtures
import constants
from authomatic.providers import oauth2


conf = fixtures.get_configuration('google')

LINK = 'https://plus.google.com/' + conf.user_id

CONFIG = {
    'class_': oauth2.Google,
    'scope': oauth2.Google.user_info_scope,
    'fixture': fixtures.providers.GoogleFixture(conf.user_login,
                                                conf.user_password),
    'offline': True,
    'user': {
        'id': conf.user_id,
        'email': conf.user_email,
        'username': None,
        'name': conf.user_name,
        'first_name': conf.user_first_name,
        'last_name': conf.user_last_name,
        'nickname': None,
        'birth_date': None,
        'city': None,
        'country': None,
        'gender': conf.user_gender,
        'link': LINK,
        'locale': conf.user_locale,
        'phone': None,
        'picture': conf.user_picture,
        'postal_code': None,
        'timezone': None,
    },
    'content_should_contain': [
        conf.user_id,
        conf.user_email,
        conf.user_name, conf.user_first_name, conf.user_last_name,
        conf.user_gender,
        LINK,
        conf.user_locale,
        conf.user_picture,

        # User info JSON keys
        'sub', 'name', 'given_name', 'family_name', 'profile', 'picture',
        'email', 'email_verified', 'gender', 'locale',
    ],
    # Case insensitive
    'content_should_not_contain': [conf.user_postal_code]
                                  + conf.no_phone + conf.no_birth_date,

    # True means that any thruthy value is expected
    'credentials': {
        'token_type': 'Bearer',
        'provider_type_id': '2-8',
        '_expiration_time': True,
        'consumer_key': None,
        'provider_id': None,
        'consumer_secret': None,
        'token': True,
        'token_secret': None,
        '_expire_in': True,
        'provider_name': 'google',
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
        'refresh_token': True,
        'provider_type': True,
    },
}