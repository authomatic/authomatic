import fixtures
from authomatic.providers import openid

conf = fixtures.get_configuration('openid_livejournal')

OPENID_IDENTIFIER = 'http://{0}.livejournal.com/'.format(conf.user_login)

CONFIG = {
    'openid_identifier': OPENID_IDENTIFIER,
    'pre_login_xpaths': [
        '//*[@id="js"]/body/div[7]/header/span',
        '//*[@id="js"]/body/div[4]/header/div/nav[1]/ul[2]/li[1]/a',
    ],
    # 'login_url': 'http://www.livejournal.com/login.bml',
    'login_xpath': '//*[@id="user"]',
    'password_xpath': '//*[@id="lj_loginwidget_password"]',
    'consent_xpaths': [
        # '//*[@id="js"]/body/div[4]/div[2]/div/form/div[3]/div[2]/button',
        '//*[@id="js"]/body/div[4]/div[2]/div/div/form/table/tbody/tr/td/input[1]',
    ],
    'class_': openid.OpenID,
    'user': {
        'id': OPENID_IDENTIFIER,
        'email': None,
        'username': None,
        'name': None,
        'first_name': None,
        'last_name': None,
        'nickname': None,
        'birth_date': None,
        'city': None,
        'country': None,
        'gender': None,
        'link': None,
        'location': None,
        'locale': None,
        'phone': None,
        'picture': None,
        'postal_code': None,
        'timezone': None,
    },
}
