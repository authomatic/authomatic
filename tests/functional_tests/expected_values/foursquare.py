import fixtures
import constants
from authomatic.providers import oauth2


conf = fixtures.get_configuration('foursquare')

CONFIG = {
    'login_xpath': '//*[@id="username"]',
    'password_xpath': '//*[@id="password"]',
    'consent_xpaths': [
        '//*[@id="loginFormButton"]',
    ],
    'class_': oauth2.Foursquare,
    'scope': oauth2.Foursquare.user_info_scope,
    'user': {
        'id': conf.user_id,
        'email': conf.user_email,
        'username': None,
        'name': conf.user_name,
        'first_name': conf.user_first_name,
        'last_name': conf.user_last_name,
        'nickname': None,
        'birth_date': None,
        'city': conf.user_city,
        'country': conf.user_country,
        'gender': conf.user_gender,
        'link': None,
        'locale': None,
        'phone': conf.user_phone,
        'picture': conf.user_picture,
        'postal_code': None,
        'timezone': None,
    },
    'content_should_contain': [
        conf.user_id,
        conf.user_first_name, conf.user_last_name,
        conf.user_city, conf.user_country,
        conf.user_gender,
        conf.user_email,
        conf.user_phone,

        # User info JSON keys
        'meta', 'code', 'notifications', 'type', 'item', 'unreadCount',
        'response', 'user', 'id', 'firstName', 'lastName', 'gender',
        'relationship', 'photo', 'prefix', 'suffix', 'friends', 'count',
        'groups', 'name', 'items', 'tips', 'lists', 'homeCity', 'bio',
        'contact', 'email', 'facebook', 'twitter', 'superuser', 'default',
        'phone', 'checkinPings', 'pings', 'badges', 'badgeId', 'unlockMessage',
        'description', 'badgeText', 'image', 'sizes', 'unlocks', 'checkins',
        'createdAt', 'shout', 'timeZoneOffset', 'location', 'lat', 'lng',
        'photos', 'posts', 'textCount', 'comments', 'source', 'url',
        'mayorships', 'venue', 'formattedPhone', 'facebookName', 'address',
        'postalCode', 'cc', 'city', 'state', 'country', 'formattedAddress',
        'categories', 'pluralName', 'shortName', 'icon', 'primary', 'verified',
        'stats', 'checkinsCount', 'usersCount', 'tipCount', 'like', 'likes',
        'width', 'height', 'visibility', 'following', 'requests', 'editable',
        'public', 'collaborative', 'canonicalUrl', 'followers', 'listItems',
        'checkin', 'scores', 'recent', 'max', 'goal', 'blockedStatus',
        'referralId'
    ],
    # Case insensitive
    'content_should_not_contain': conf.no_birth_date +
        [
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