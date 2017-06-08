# -*- coding: utf-8 -*-
import datetime

# from pyvirtualdisplay import Display
from selenium import webdriver

import constants

# Choose and configure the browser of your choice
def get_browser():
    return webdriver.Chrome()
    # global display
    #
    # display = Display(visible=0, size=(1024, 768))
    # display.start()
    # return webdriver.Firefox()


def teardown():
    pass
    # global display
    # display.stop()


# A failed login by a provider will be retried so many times as set here
MAX_LOGIN_ATTEMPTS = 3
# Multiplies the wait times set in expected values
WAIT_MULTIPLIER = 1
# Minimum wait time
MIN_WAIT = 0

# The host and port where the tested ap shoud listen.
HOST = '127.0.0.1'
PORT = 80

# The host alias set in the /etc/hosts file.
# The actual tests will navigate selenium browser to this host.
# This is necessary because some providers don't support localhost as the
# callback url.
HOST_ALIAS = 'authomatic.org'

# Only frameworks included here will be tested.
INCLUDE_FRAMEWORKS = [
    # 'django',
    'flask',
    # 'pyramid',
]

# Only providers included here will be tested.
# This is a convenience to easily exclude providers from tests by commenting
# them out.
INCLUDE_PROVIDERS = [
    # 'bitbucket',
    # 'flickr',
    # # Meetup has a bug in its OAuth 1.0a flow:
    # # https://github.com/meetup/api/issues/83
    # 'meetup',
    # 'plurk',
    # 'twitter',
    # 'tumblr',
    # # UbuntuOne service is no longer available
    # 'ubuntuone',
    # 'vimeo',
    # 'xero',
    # 'xing',
    # 'yahoo',
    #
    # 'amazon',
    # # 'behance', # Behance doesn't support third party authorization anymore.
    # 'bitly',
    # 'deviantart',
    # 'eventbrite',
    # 'facebook',
    # 'foursquare',
    # 'google',
    # 'github',
    # 'linkedin',
    # 'paypal',
    # 'reddit',
    # 'vk',
    # 'windowslive',
    # 'yammer',
    # 'yandex',
    #
    # 'openid_livejournal',
    # 'openid_verisignlabs',
    # 'openid_wordpress',
    # 'openid_yahoo',
]


# Use these constants if you have the same user info by all tested providers.
PASSWORD = '1Kokotina'
EMAIL = 'peterhudec@peterhudec.com'
FIRST_NAME = 'Peter'
LAST_NAME = 'Hudec'
NAME = FIRST_NAME + ' ' + LAST_NAME
USERNAME = 'peterhudec'
USERNAME_REVERSE = 'hudecpeter'
NICKNAME = 'hudo'
BIRTH_YEAR = 1979
BIRTH_MONTH = 11
BIRTH_DAY = 18
BIRTH_DATE = datetime.datetime(BIRTH_YEAR, BIRTH_MONTH, BIRTH_DAY)
CITY = 'Bratislava'
COUNTRY = 'Slovakia'
COUNTRY_ISO2 = 'sk'
POSTAL_CODE = '82107'
PHONE = '0903972845'
PHONE_INTERNATIONAL = '00421903972845'
GENDER = constants.GENDER_MALE
LOCALE = 'en_US'
LOCATION = CITY + ', ' + COUNTRY

# Common values for all providers
COMMON = {
    # Could be same if the user sets it so
    'user_birth_date': BIRTH_DATE,
    'user_birth_day': BIRTH_DAY,
    'user_birth_month': BIRTH_MONTH,
    'user_birth_year': BIRTH_YEAR,
    'user_login': EMAIL,
    'user_password': PASSWORD,
    'user_email': EMAIL,
    'user_first_name': FIRST_NAME,
    'user_last_name': LAST_NAME,
    'user_name': NAME,
    'user_username': USERNAME,
    'user_username_reverse': USERNAME_REVERSE,
    'user_nickname': NICKNAME,
    'user_city': CITY,
    'user_country': COUNTRY,
    'user_gender': GENDER,
    'user_phone': PHONE,
    'user_postal_code': POSTAL_CODE,
    'user_locale': LOCALE,
    'user_location': LOCATION,

    # Provider and user specific value
    # 'user_id': '',
    # 'user_locale': None,
    # 'user_timezone': None,

    # Provider specific format
    # 'user_picture': '',
    # 'user_link': '',

    # Provider specific value
    # 'consumer_key': '',
    # 'consumer_secret': '',
}

# Values from COMMON will be overriden by values from PROVIDERS[provider_name]
# if set.
PROVIDERS = {
    # OAuth 1.0a
    'bitbucket': {
        'consumer_key': 'pusFTPPcYe7UjdPLeb',
        'consumer_secret': 'xHMUxrqZqM2bZ7UPdu85y2fyffYsKJzq',
        'user_id': USERNAME,
        'user_password': 'edenbedenAtlassianHreben8'
    },
    'flickr': {
        'consumer_key': '518b447b07302e1a96cd0c4db9ae7580',
        'consumer_secret': 'b9b34d4b31d98b3d',
        'user_login': USERNAME_REVERSE,
        'user_id': '38774396@N06',
        'user_username': NAME,
    },
    'meetup': {
        'consumer_key': 's5ke2j3rfjnb3famghelr4cakh',
        'consumer_secret': 'imemaigvgjh9n44vtv89gr5uv9',
        'user_login': EMAIL,
        'user_id': '84631542',
        'user_country': COUNTRY_ISO2,
        'user_location': '{0}, {1}'.format(CITY, COUNTRY_ISO2),
    },
    'plurk': {
        'consumer_key': 't4kdmAEUZfxe',
        'consumer_secret': 'SabRa44lgMTt69gpLq7pcxYIFUTHSu1u',
        'user_id': '9433315',
        'user_gender': '1',
        'user_locale': 'en',
        'user_nickname': USERNAME,
        'user_country': 'Slovak Republic',
        'user_location': 'Bratislava, Slovak Republic',
        'user_timezone': 'UTC',
    },
    'twitter': {
        'consumer_key': 'zku3BZ9wi7e4e07h0M3VA',
        'consumer_secret': 'WQ0SYSUWXlBiLvYAJ32DDMfwsJ4up79EfifNXks',
        'user_id': '243645555',
        'user_password': PASSWORD,
        # TODO: Change to regex
        'user_link': 'http://t.co/2DHh59Jg',
        'user_picture': 'http://pbs.twimg.com/profile_images/1815572456/ja_normal.jpg',
        'user_username': 'peterhudec_com',
        'user_locale': 'en',
    },
    'tumblr': {
        'consumer_key': 'MEVRboAn9x7zEayX8QKUrxiOgkPJqv0BSijvplzL4KxXBDeGoC',
        'consumer_secret': 'tWT7sWoF9gI1pZ7guNH5KEW2K4vDVes7jikhHNVcDqoGqEefaZ',
        'user_id': USERNAME,
        'user_name': USERNAME,
    },
    'vimeo': {
        'consumer_key': '8e8730d3bb2a15b6d172bfa8e8bd82cafe66e62b',
        'consumer_secret': 'J8G43W6B75i8W84vz2epyU0ztkTrlxwH8/Jdo8qpvdx7r1A3RPPg82dgwR094Hlp4H1Jw4MOQJLzS+pyX64pX5fydqi98FEgmGXdGQ1+odfmImt91PGbkmH2AOddZHQ7',
        'user_id': '16990697',
    },
    'xero': {
        'consumer_key': 'LSDLAW8H3DRFGTBBCIKOQQOWOJTY2J',
        'consumer_secret': 'INAULZZWB2X5JEDWKKXRGZK0SCREYI',
        'user_id': '0c604bb8-7598-472e-90ce-a69e0fc20cd8',
    },
    'xing': {
        'consumer_key': 'aed27cac96f05dff725a',
        'consumer_secret': '41778fef68e84fa7082e18fca6b9c7eb2ac4482e',
        'user_id': '20439769_c51b8d',
        'user_username': 'Peter_Hudec4',
        'user_country': COUNTRY_ISO2.upper(),
        'user_gender': 'm',  # m or f
        'user_locale': 'en',
        'user_location': '{0}, {1}'.format(CITY, COUNTRY_ISO2.upper()),
        'user_timezone': 'Europe/Bratislava',
        'user_phone': '421903972845',
    },
    'yahoo': {
        'consumer_key': 'dj0yJmk9cU1wQ3N2aTFlYzlXJmQ9WVdrOVlrZFdiVzVCTkdNbWNHbzlNVE16TVRFNU5ERTJNZy0tJnM9Y29uc3VtZXJzZWNyZXQmeD03Mw--',
        'consumer_secret': '41cb637f38ff5225a20f4e2b9c321eb96cdea6ee',
        'user_login': USERNAME_REVERSE,
        'user_id': 'OV6YUPBP7S5FI25QLNJ3BNP5BY',
        'user_gender': 'M' # M or F
    },

    # OAuth 2.0
    'amazon': {
        'consumer_key': 'amzn1.application-oa2-client.aac94a29737c4d86a734e5964696d2bd',
        'consumer_secret': 'bb1aa3772cd755d009ba419211fccde1e785021e1bbea4334235ca298dac42b0',
        'user_id': 'amzn1.account.AFQXBE5AJMX73ZABIBYD25ET2MZQ',
        'user_password': '19Pitelova79',
    },
    'behance': {
        'consumer_key': 'J6MwhGHdTHwwYQEHyTq2jNgly0EEXixe',
        'consumer_secret': 'A3IP7wH2pZ0zpiCCCYwO.Z7HkK',
        'user_id': '???',
    },
    'bitly': {
        'consumer_key': 'd4afbd49a8abfbbf288730725dd9609dbb167320',
        'consumer_secret': 'cd30cb160445410d2825aed974ae5fdb15a3db9b',
        'user_id': 'o_a1o5pegh9',
    },
    'deviantart': {
        'consumer_key': '376',
        'consumer_secret': 'd56ec842a9558fe9916210b376988c2d',
    },
    'eventbrite': {
        'consumer_key': 'M5T4QRF5TNIQQJ76EC',
        'consumer_secret': 'C4HNTPVUKCMK3XBWQJ45KFV5H2AIII5C7XNNPZIYSQIQAPMQP7',
        'user_id': '125996068589',
    },
    'facebook': {
        'consumer_key': '482771598445314',
        'consumer_secret': '7163e6e8dedc2c055445b553823ec910',
        'user_id': '737583375',
        'user_password': 'kokotina',
        # This changes when switching from and to Daylight Saving Time
        # 'user_timezone': '2',
    },
    'foursquare': {
        'consumer_key': '11Q4GU3IGQYN3QTR5542VAGE1ZCQD5QDAOXVR1LA3FZ3Q24Z',
        'consumer_secret': 'WN1HYN4W0QJ4H0YV2KET1XKJHA1W2PFQT4WFOKDG3J3T05GK',
        'user_id': '8698379',
        'user_country': u'Slovenská republika',
        'user_location': u'Bratislava, Slovenská republika',
        'user_picture': 'https://irs2.4sqi.net/img/user/SEG1MMJYH0XHZTSY.jpg',
    },
    'google': {
        'consumer_key': '75167970188.apps.googleusercontent.com',
        'consumer_secret': 'Y70ZmvlkMKOTB8kKGBgN_BME',
        'user_login': 'peterhudec.com@gmail.com',
        'user_id': '117034840853387702598',
        'user_password': 'google19Pitelova79',
        'user_email': 'peterhudec.com@gmail.com',
        'user_locale': 'en',
        'user_picture': ('https://lh5.googleusercontent.com/-LbPepOoFAfA/'
                         'AAAAAAAAAAI/AAAAAAAAOWY/3rWutUjFRGw/photo.jpg?sz=50'),
    },
    'github': {
        'user_login': 'peterhudec@peterhudec.com',
        'user_password': 'edenbedenGithubHreben8',
        'consumer_key': '4dde1fd8f548bfe87f0c',
        'consumer_secret': '05ee98945b55fc214a6d1d0c30abee12c3044e12',
        'user_id': '2333157',
        'access_headers': {'User-Agent': ('Authomatic.py Automated Functional '
                                          'Tests')},
        'user_country': 'United Kingdom',
        'user_city': 'London',
        'user_location': 'London, UK',
    },
    'linkedin': {
        'consumer_key': '771ej662emreyu',
        'consumer_secret': 'g3AMiN2vid6Dnn7Q',
        'user_id': 'nqpJbN5wLs',
        'user_country': 'Slovak Republic',
        'user_location': COUNTRY_ISO2,
        'user_link': 'https://www.linkedin.com/in/phudec',
    },
    'paypal': {
        'consumer_key': 'AR58GRBgr81q6vZQOUxwB1OF9_62PXb1CouQVaENf5dbTLgPkr3K7YZXgnc6',
        'consumer_secret': 'EJqCvRAZ4sFobX_NlzyVMyD3PSXH41pAWpeCFpiepworglq_f_5dl3TrCYFl',
    },
    'reddit': {
        'consumer_key': 'Jx3WyR5xS4pm1A',
        'consumer_secret': 'Z0RWV65T5e-qKf0OHDIu1baKhrI',
        'user_login': USERNAME,
        'user_id': 'aurmu',
        'access_headers': {'User-Agent': ('Authomatic.py Automated Functional '
                                          'Tests')}
    },
    # 'viadeo': {
    #     'consumer_key': 'AuthomaticDevNyWlGx',
    #     'consumer_secret': 'NvQuiowaMRBcs',
    # },
    'vk': {
        'consumer_key': '3479081',
        'consumer_secret': '3QKH4U5tpKytUYDGMWbO',
        'user_id': '203822236',
        'user_city': '1908070',
        'user_country': '184',
        'user_location': '1908070, 184',
        'user_gender': '2',
        'user_picture': 'http://cs7010.vk.me/c619226/v619226236/57a1/LJ4KAzr-byY.jpg',
        'user_timezone': '1',
    },
    'windowslive': {
        'consumer_key': '00000000440E8C5B',
        'consumer_secret': 'gu57AluGQnMkzxzdVp0ficFC00pBkl4S',
        'user_id': '5706420657626adb',
    },
    'yammer': {
        'consumer_key': '9JsB3qvVnptaR8GOkfA',
        'consumer_secret': 'Rt11EFemrHIZ6VY8pk8K4CvovTM6Y4hQmo8E3HDKY',
        'user_id': '1496566333',
        'user_picture': ('https://mug0.assets-yammer.com/mugshot/images/48x48/'
                         'gWV0tl9Ln-NvG4V5-1rghnNwzxkBGfbn'),
        'user_timezone': 'Pacific Time (US & Canada)',
        'user_locale': 'en-US',
    },
    'yandex': {
        'consumer_key': '9c77329488b24bc6b8edb66777e1236a',
        'consumer_secret': '4b4408cda2f0459fab278b0880ebcf4d',
        'user_login': USERNAME,
        'user_id': '203067641',
    },

    # OpenID
    'openid_yahoo': {
        'openid_identifier': 'me.yahoo.com',
        'user_id': 'https://me.yahoo.com/a/w04F2kgxq.RX.VjfbCiOuQ0CwmbG8Qs-',
        'user_login': USERNAME_REVERSE,
        'user_email': 'hudecpeter@yahoo.com',
    },
    'openid_livejournal': {
        'openid_identifier': '{0}.livejournal.com'.format(USERNAME),
        'user_login': USERNAME,
        'user_id': 'http://{0}.livejournal.com/'.format(USERNAME)
    },
    'openid_wordpress': {
        'openid_identifier': '{0}.wordpress.com'.format(USERNAME),
        'user_login': EMAIL,
        'user_id': 'https://{0}.wordpress.com/'.format(USERNAME),
        'user_nickname': 'veporclique',
    },
    'openid_verisignlabs': {
        'openid_identifier': '{0}.pip.verisignlabs.com'.format(USERNAME),
        'user_login': USERNAME,
        'user_id': 'http://{0}.pip.verisignlabs.com/'.format(USERNAME),
        'user_nickname': NICKNAME,
        'user_timezone': 'Europe/Bratislava',
        'user_locale': 'Slovak',
        'user_gender': 'M',
    },
}
