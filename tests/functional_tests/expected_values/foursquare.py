# -*- coding: utf-8 -*-
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
        'address', 'allowMenuUrlEdit', 'bio', 'birthday', 'blockedStatus',
        'canonicalUrl', 'categories', 'cc', 'checkin', 'checkinPings',
        'checkins', 'checkinsCount', 'city', 'code', 'collaborative',
        'comments', 'contact', 'count', 'country', 'createdAt', 'default',
        'description', 'editable', 'email', 'entities', 'facebook',
        'facebookName', 'firstName', 'formattedAddress', 'formattedPhone',
        'friends', 'gender', 'groups', 'height', 'homeCity', 'icon', 'id',
        'isMayor', 'item', 'items', 'lastName', 'lat', 'lenses', 'like',
        'likes', 'listItems', 'lists', 'lng', 'location', 'mayorships', 'meta',
        'name', 'neighborhood', 'notifications', 'phone', 'photo', 'photos',
        'pings', 'pluralName', 'postalCode', 'posts', 'prefix', 'primary',
        'public', 'referralId', 'relationship', 'requestId', 'requests',
        'response', 'shortName', 'shout', 'source', 'state', 'stats', 'suffix',
        'superuser', 'textCount', 'timeZoneOffset', 'tipCount', 'tips',
        'twitter', 'type', 'unreadCount', 'url', 'user', 'usersCount', 'venue',
        'verified', 'verifiedPhone', 'visibility', 'width'
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
