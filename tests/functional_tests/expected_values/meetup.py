import re

import fixtures
import constants
from authomatic.providers import oauth1

conf = fixtures.get_configuration('meetup')

LINK = 'http://www.meetup.com/members/{0}'.format(conf.user_id)
PICTURE = re.compile(r'http://photos\d+.meetupstatic.com/photos/member/'
                     r'\w/\d+/\w/\d+/member_\d+.jpeg')

CONFIG = {
    'login_xpath': '//*[@id="email"]',
    'password_xpath': '//*[@id="password"]',
    'consent_xpaths': [],
    'class_': oauth1.Meetup,
    'user': {
        'birth_date': None,
        'city': conf.user_city,
        'country': conf.user_country,
        'email': None,
        'gender': None,
        'id': conf.user_id,
        'first_name': None,
        'last_name': None,
        'link': LINK,
        'locale': conf.user_locale,
        'location': conf.user_location,
        'name': conf.user_name,
        'nickname': None,
        'phone': None,
        'picture': PICTURE,
        'postal_code': None,
        'timezone': None,
        'username': None,
    },
    'content_should_contain': [
        conf.user_city,
        conf.user_country,
        conf.user_id,
        LINK.replace('/', '\/'),
        conf.user_locale,
        conf.user_name,

        # User info JSON keys
        'city', 'common', 'country', 'id', 'joined', 'lang', 'lat', 'link',
        'lon', 'name', 'other_services', 'photo', 'photo_id', 'photo_link',
        'self', 'status', 'thumb_link', 'topics', 'urlkey', 'visited'
    ],
    # Case insensitive
    'content_should_not_contain':
        conf.no_birth_date +
        conf.no_email +
        conf.no_gender +
        ['first_name', 'firstname', 'last_name', 'lastname'] +
        conf.no_nickname +
        conf.no_phone +
        conf.no_postal_code +
        conf.no_timezone +
        conf.no_username,
    # True means that any thruthy value is expected
    'credentials': {
        '_expiration_time': None,
        '_expire_in': True,
        'consumer_key': True,
        'consumer_secret': True,
        'provider_id': None,
        'provider_name': 'meetup',
        'provider_type': 'authomatic.providers.oauth1.OAuth1',
        'provider_type_id': '1-3',
        'refresh_status': constants.CREDENTIALS_REFRESH_NOT_SUPPORTED,
        'refresh_token': None,
        'token': True,
        'token_secret': True,
        'token_type': None,
    },
}