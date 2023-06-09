# -*- coding: utf-8 -*-
import fixtures
import constants
from authomatic.providers import oauth2


conf = fixtures.get_configuration('paypal')

CONFIG = {
    'logout_url': 'https://www.paypal.com/sk/cgi-bin/webscr?cmd=_logout',
    'class_': oauth2.PayPal,
    'scope': oauth2.PayPal.user_info_scope,
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
        'location': None,
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
    # True means that any truthy value is expected
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
