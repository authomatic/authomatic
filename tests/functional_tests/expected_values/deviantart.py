import fixtures
import constants
from authomatic.providers import oauth2


conf = fixtures.get_configuration('deviantart')

PICTURE = 'http://a.deviantart.net/avatars/p/e/{0}.jpg?1'\
    .format(conf.user_username)

CONFIG = {
    'pre_login_xpaths': [
        '//*[@id="joinform"]/fieldset/small/a'
    ],
    'login_xpath': '//*[@id="username"]',
    'password_xpath': '//*[@id="password"]',
    'consent_xpaths': [
        '//*[@id="terms_agree"]',
        '//*[@id="authorize_form"]/fieldset/div[2]/div[2]/a[1]',
    ],
    # 'consent_wait_seconds': 2,
    'access_headers': {
        'User-Agent': 'Authomatic.py Automated Functional Tests',
    },
    'class_': oauth2.DeviantART,
    'scope': oauth2.DeviantART.user_info_scope,
    'user': {
        'id': None,
        'email': None,
        'username': conf.user_username,
        'name': conf.user_username,
        'first_name': None,
        'last_name': None,
        'nickname': None,
        'birth_date': None,
        'city': None,
        'country': None,
        'gender': None,
        'link': None,
        'locale': None,
        'location': None,
        'phone': None,
        'picture': PICTURE,
        'postal_code': None,
        'timezone': None,
    },
    'content_should_contain': [
        conf.user_username,

        # User info JSON keys
        'username', 'symbol', 'usericonurl',
    ],
    # Case insensitive
    'content_should_not_contain': conf.no_phone + conf.no_birth_date +
                                  conf.no_email + conf.no_location +
                                  conf.no_gender + conf.no_locale +
                                  conf.no_first_name + conf.no_last_name,
    # True means that any thruthy value is expected
    'credentials': {
        'token_type': 'Bearer',
        'provider_type_id': '2-4',
        '_expiration_time': True,
        'consumer_key': None,
        'provider_id': None,
        'consumer_secret': None,
        'token': True,
        'token_secret': None,
        '_expire_in': True,
        'provider_name': 'deviantart',
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
        '_expiration_time': None,
        'consumer_key': True,
        'provider_id': True,
        'consumer_secret': True,
        'token': False,
        'token_secret': True,
        '_expire_in': None,
        'provider_name': True,
        'refresh_token': False,
        'provider_type': True,
    },
}