import re

import fixtures
from authomatic.providers import openid

conf = fixtures.get_configuration('openid_verisignlabs')

OPENID_IDENTIFIER = 'http://{0}.pip.verisignlabs.com/'.format(conf.user_login)

CONFIG = {
    'openid_identifier': OPENID_IDENTIFIER,
    'logout_url': 'https://pip.verisignlabs.com/logout.do',
    'login_xpath': '//*[@id="mainbody"]/form/table/tbody/tr[2]/td[2]/input',
    'password_xpath': '//*[@id="mainbody"]/form/table/tbody/tr[3]/td[2]/input',
    'consent_xpaths': [
        '//*[@id="TrustAuthenticateExchange"]/div[2]/input[2]',
    ],
    'alert_wait_seconds': 1,
    'class_': openid.OpenID,
    'user': {
        'id': OPENID_IDENTIFIER,
        'email': conf.user_email,
        'username': None,
        'name': conf.user_name,
        'first_name': None,
        'last_name': None,
        'nickname': conf.user_nickname,
        'birth_date': conf.user_birth_date_str,
        'city': None,
        'country': conf.user_country,
        'gender': re.compile(r'^\w{1}$'),
        'link': None,
        'location': conf.user_country,
        'locale': re.compile(r'^\w+$'),
        'phone': None,
        'picture': None,
        'postal_code': conf.user_postal_code,
        'timezone': re.compile(r'^\w+/\w+$'),
    },
}