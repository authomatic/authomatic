import fixtures
import constants
from authomatic.providers import oauth2

conf = fixtures.get_configuration('amazon')


CONFIG = {
    'login_xpath': '//*[@id="ap_email"]',
    'password_xpath': '//*[@id="ap_password"]',
    'consent_xpaths': [
        '//*[@id="signInSubmit"]/span/button',
        '//*[@id="ap-oaconsent-agree-button"]/span/button',
    ],
    'class_': oauth2.Amazon,
    'scope': oauth2.Amazon.user_info_scope,
    'user': {
        'birth_date': None,
        'city': None,
        'country': None,
        'email': conf.user_email,
        'first_name': None,
        'gender': None,
        'id': conf.user_id,
        'last_name': None,
        'link': None,
        'locale': None,
        'name': conf.user_name,
        'nickname': None,
        'phone': None,
        'picture': None,
        # You need to have default shipping address set in your Amazon account:
        # https://www.amazon.com/gp/css/account/address/view.html?ie=UTF8&ref_=ya_manage_address_book_t1&
        'postal_code': conf.user_postal_code,
        'timezone': None,
        'username': None,
    },
    'content_should_contain': [
        conf.user_email,
        conf.user_name,
        conf.user_id,
        conf.user_postal_code,

        # User info JSON keys
        'email', 'name', 'user_id', 'postal_code'
    ],
    # Case insensitive
    'content_should_not_contain':
        conf.no_birth_date +
        conf.no_city +
        conf.no_first_name +
        conf.no_last_name +
        conf.no_gender +
        conf.no_locale +
        conf.no_nickname +
        conf.no_phone +
        conf.no_timezone +
        conf.no_username
        ,
    # True means that any thruthy value is expected
    'credentials': {
        'token_type': 'Bearer',
        'provider_type_id': '2-18',
        '_expiration_time': True,
        'consumer_key': None,
        'provider_id': None,
        'consumer_secret': None,
        'token': True,
        'token_secret': None,
        '_expire_in': '3600',
        'provider_name': 'amazon',
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