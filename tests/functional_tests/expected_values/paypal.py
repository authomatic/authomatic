import fixtures
from fixtures.providers import BaseProviderFixture
import constants
from authomatic.providers import oauth2


class LoginFixture(BaseProviderFixture):
    LOGIN_XPATH = None
    PASSWORD_XPATH = None
    CONSENT_XPATHS = None


conf = fixtures.get_configuration('paypal')


CONFIG = {
    'class_': oauth2.PayPal,
    'scope': oauth2.PayPal.user_info_scope,
    'fixture': LoginFixture(conf.user_login, conf.user_password),
    'user': {
        'birth_date': None,
        'city': None,
        'country': None,
        'email': None,
        'first_name': None,
        'gender': None,
        'id': None,
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
    'content_should_contain': [],
    # Case insensitive
    'content_should_not_contain': [],
    # True means that any thruthy value is expected
    'credentials': {
        'token_type': 'Bearer',
        'provider_type_id': '2-10',
        '_expiration_time': True,
        'consumer_key': None,
        'provider_id': None,
        'consumer_secret': None,
        'token': True,
        'token_secret': None,
        '_expire_in': True,
        'provider_name': 'paypal',
        'refresh_token': None,
        'provider_type': 'authomatic.providers.oauth2.OAuth2',
        'refresh_status': constants.CREDENTIALS_REFRESH_NOT_SUPPORTED,
    },
}