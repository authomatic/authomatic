import calendar
import re

import fixtures
import constants
from authomatic.providers import oauth2


conf = fixtures.get_configuration('foursquare')

CONFIG = {
    'logout_url': 'https://foursquare.com/logout',
    'login_xpath': '//*[@id="username"]',
    'password_xpath': '//*[@id="password"]',
    'consent_xpaths': [],
    'class_': oauth2.Foursquare,
    'scope': oauth2.Foursquare.user_info_scope,
    'user': {
        'birth_date': conf.user_birth_date_str,
        'city': conf.user_city,
        'country': conf.user_country,
        'email': conf.user_email,
        'first_name': conf.user_first_name,
        'gender': conf.user_gender,
        'id': conf.user_id,
        'last_name': conf.user_last_name,
        'link': None,
        'locale': None,
        'location': conf.user_location,
        'name': conf.user_name,
        'nickname': None,
        'phone': conf.user_phone,
        'picture': re.compile(r'^https://\w+\.\w+\.net/img/user/\w+\.jpg$'),
        'postal_code': None,
        'timezone': None,
        'username': None,
    },
    'content_should_contain': [
        str(calendar.timegm(conf.user_birth_date.timetuple())),  # Timestamp
        conf.user_city,
        conf.user_country,
        conf.user_email,
        conf.user_first_name,
        conf.user_gender,
        conf.user_id,
        conf.user_last_name,
        conf.user_phone,

        # User info JSON keys
        'meta', 'code', 'notifications', 'type', 'item', 'unreadCount',
        'response', 'user', 'id', 'firstName', 'lastName', 'gender',
        'relationship', 'photo', 'prefix', 'suffix', 'friends', 'count',
        'groups', 'name', 'items', 'tips', 'lists', 'homeCity', 'bio',
        'contact', 'email', 'facebook', 'twitter', 'superuser', 'default',
        'birthday', 'phone', 'checkinPings', 'pings', 'badges', 'badgeId',
        'unlockMessage', 'description', 'badgeText', 'image', 'sizes',
        'unlocks', 'checkins', 'createdAt', 'shout', 'timeZoneOffset',
        'location', 'lat', 'lng', 'photos', 'posts', 'textCount', 'comments',
        'source', 'url', 'mayorships', 'venue', 'formattedPhone',
        'facebookName', 'address', 'postalCode', 'cc', 'neighborhood', 'city',
        'state', 'country', 'formattedAddress', 'categories', 'pluralName',
        'shortName', 'icon', 'primary', 'verified', 'stats', 'checkinsCount',
        'usersCount', 'tipCount', 'like', 'likes', 'width', 'height',
        'visibility', 'requests', 'editable', 'public', 'collaborative',
        'canonicalUrl', 'followers', 'listItems', 'checkin', 'blockedStatus',
        'referralId'
    ],
    # Case insensitive
    'content_should_not_contain': [
        'locale',
        'language',
        'deprecated',
        conf.user_postal_code,
        conf.user_username_reverse
    ],
    # True means that any thruthy value is expected
    'credentials': {
        'token_type': None,
        'provider_type_id': '2-6',
        '_expiration_time': None,
        'consumer_key': None,
        'provider_id': None,
        'consumer_secret': None,
        'token': True,
        'token_secret': None,
        '_expire_in': True,
        'provider_name': 'foursquare',
        'refresh_token': None,
        'provider_type': 'authomatic.providers.oauth2.OAuth2',
        'refresh_status': constants.CREDENTIALS_REFRESH_NOT_SUPPORTED,
    },
}