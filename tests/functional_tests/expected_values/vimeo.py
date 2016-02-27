import re

import fixtures
import constants
from authomatic.providers import oauth1

conf = fixtures.get_configuration('vimeo')
LINK = 'http://vimeo.com/user{0}'.format(conf.user_id)
PICTURE = re.compile(r'http://\w+.vimeocdn.com/portrait/\d+_300x300.jpg')


CONFIG = {
    'logout_url': 'https://vimeo.com/log_out',
    'login_xpath': '//*[@id="signup_email"]',
    'password_xpath': '//*[@id="login_password"]',
    'consent_xpaths': [
        '//*[@id="security"]/form/input[4]',
    ],
    'class_': oauth1.Vimeo,
    'user': {
        'birth_date': None,
        'city': None,
        'country': None,
        'email': None,
        'gender': None,
        'id': conf.user_id,
        'first_name': None,
        'last_name': None,
        'link': LINK,
        'locale': None,
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
        conf.user_id,
        LINK.replace('/', '\/'),
        conf.user_location,
        conf.user_name,

        # User info JSON keys
        'bio', 'created_on', 'display_name', 'id', 'is_plus', 'is_pro',
        'is_staff', 'location', 'portrait_huge', 'portrait_large',
        'portrait_medium', 'portrait_small', 'profile_url', 'total_albums',
        'total_channels', 'total_contacts', 'total_videos_appears_in',
        'total_videos_liked', 'total_videos_uploaded', 'url', 'videos_url'
    ],
    # Case insensitive
    'content_should_not_contain':
        conf.no_birth_date +
        ['city', 'country'] +
        conf.no_email +
        conf.no_gender +
        conf.no_locale +
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
        'provider_name': 'vimeo',
        'provider_type': 'authomatic.providers.oauth1.OAuth1',
        'provider_type_id': '1-8',
        'refresh_status': constants.CREDENTIALS_REFRESH_NOT_SUPPORTED,
        'refresh_token': None,
        'token': True,
        'token_secret': True,
        'token_type': None,
    },
}