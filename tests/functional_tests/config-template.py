import constants

# The host and port where the tested ap shoud listen.
HOST = '127.0.0.1'
PORT = 8080

# The host alias set in the /etc/hosts file.
# The actual tests will navigate selenium browser to this host.
# This is necessary because some providers don't support localhost as the
# callback url.
HOST_ALIAS = 'authomatic.com'

# Only providers included here will be tested.
# This is a convenience to easily exclude providers from tests by commenting
# them out.
INCLUDE_PROVIDERS = [
    'bitly',
    'deviantart',
    'facebook',
    'foursquare',
    'google',
]

# Use these constants if you have the same user info by all tested providers.
PASSWORD = '##########'
EMAIL = 'andy.pipkin@littlebritain.co.uk'
FIRST_NAME = 'Andy'
LAST_NAME = 'Pipkin'
NAME = FIRST_NAME + ' ' + LAST_NAME
USERNAME = 'andypipkin'
USERNAME_REVERSE = 'pipkinandy'
NICKNAME = 'MR. Pipkin'
BIRTH_YEAR = '1979'
CITY = 'London'
COUNTRY = 'Great Britain'
POSTAL_CODE = 'EC1A1DH'
PHONE = '??????????'
GENDER = constants.GENDER_MALE
LOCALE = 'en_UK'

# Common values for all providers
COMMON = {
    # Could be same if the user sets it so
    'user_login': EMAIL,
    'user_password': PASSWORD,
    'user_email': EMAIL,
    'user_first_name': FIRST_NAME,
    'user_last_name': LAST_NAME,
    'user_name': NAME,
    'user_username': USERNAME,
    'user_username_reverse': USERNAME_REVERSE,
    'user_nickname': NICKNAME,
    'user_birth_year': BIRTH_YEAR,
    'user_city': CITY,
    'user_country': COUNTRY,
    'user_gender': GENDER,
    'user_phone': PHONE,
    'user_postal_code': POSTAL_CODE,
    'user_locale': LOCALE,

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
    'bitly': {
        'consumer_key': '##########',
        'consumer_secret': '##########',
        'user_id': '##########',
    },
    'deviantart': {
        'consumer_key': '##########',
        'consumer_secret': '##########',
    },
    'facebook': {
        'consumer_key': '##########',
        'consumer_secret': '##########',
        'user_id': '##########',
        'user_password': '##########',
        # This changes when switching from and to Daylight Saving Time
        'user_timezone': '??????????',
    },
    'foursquare': {
        'consumer_key': '##########',
        'consumer_secret': '##########',
        'user_id': '??????????',
        'user_country': '??????????',
        'user_picture': '??????????',
    },
    'google': {
        'consumer_key': '##########',
        'consumer_secret': '##########',
        'user_id': '##########',
        'user_password': '##########',
        'user_email': '##########',
        'user_locale': '##########',
        'user_picture': ('??????????'),
    },
}
