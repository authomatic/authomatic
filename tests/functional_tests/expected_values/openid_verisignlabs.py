import fixtures
from authomatic.providers import openid

conf = fixtures.get_configuration('openid_verisignlabs')

CONFIG = {
    'login_xpath': '//*[@id="mainbody"]/form/table/tbody/tr[2]/td[2]/input',
    'password_xpath': '//*[@id="mainbody"]/form/table/tbody/tr[3]/td[2]/input',
    'consent_xpaths': [
        '//*[@id="TrustAuthenticateExchange"]/div[2]/input[2]'
    ],
    'alert_wait_seconds': 1,
    'class_': openid.OpenID,
    'user': {
        'id': conf.user_id,
        'email': conf.user_email,
        'username': None,
        'name': conf.user_name,
        'first_name': None,
        'last_name': None,
        'nickname': conf.user_nickname,
        'birth_date': conf.user_birth_date_str,
        'city': None,
        'country': conf.user_country,
        'gender': conf.user_gender,
        'link': None,
        'location': conf.user_country,
        'locale': conf.user_locale,
        'phone': None,
        'picture': None,
        'postal_code': conf.user_postal_code,
        'timezone': conf.user_timezone,
    },
}