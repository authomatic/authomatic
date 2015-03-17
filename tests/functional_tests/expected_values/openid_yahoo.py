import re

import fixtures
import constants
from authomatic.providers import openid

conf = fixtures.get_configuration('openid_yahoo')

CONFIG = {
    'login_xpath': '//*[@id="login-username"]',
    'password_xpath': '//*[@id="login-passwd"]',
    'consent_xpaths': [
        '//*[@id="login-signin"]'
    ],
    'class_': openid.OpenID,
    'user': {
        'id': conf.user_id,
        'email': conf.user_email,
        'username': None,
        'name': conf.user_name,
        'first_name': None,
        'last_name': None,
        'nickname': None,
        'birth_date': None,
        'city': None,
        'country': None,
        'gender': None,
        'link': None,
        'locale': None,
        'phone': None,
        'picture': None,
        'postal_code': None,
        'timezone': None,
    },
}