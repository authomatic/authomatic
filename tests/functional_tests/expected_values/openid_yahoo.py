# -*- coding: utf-8 -*-
import fixtures
from authomatic.providers import openid

conf = fixtures.get_configuration('openid_yahoo')

CONFIG = {
    'openid_identifier': 'me.yahoo.com',
    'login_xpath': '//*[@id="login-username"]',
    'password_xpath': '//*[@id="login-passwd"]',
    'enter_after_login_input': True,
    'before_password_input_wait': 1,
    'consent_xpaths': [
        '//*[@id="login-signin"]',
        '//*[@id="agree"]',
    ],
    'after_consent_wait_seconds': 1,
    'logout_url': 'https://login.yahoo.com/config/login?logout=1',
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
        'location': None,
        'phone': None,
        'picture': None,
        'postal_code': None,
        'timezone': None,
    },
}
