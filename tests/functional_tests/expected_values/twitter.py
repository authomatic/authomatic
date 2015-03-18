import fixtures
import constants
from authomatic.providers import oauth1

conf = fixtures.get_configuration('twitter')

CONFIG = {
    'login_xpath': '//*[@id="username_or_email"]',
    'password_xpath': '//*[@id="password"]',
    'consent_xpaths': [
        '//*[@id="allow"]',
    ],
    'class_': oauth1.Twitter,
    'user': {
        'birth_date': None,
        'city': conf.user_city,
        'country': conf.user_country,
        'email': None,
        'gender': None,
        'id': conf.user_id,
        'first_name': None,
        'last_name': None,
        'link': conf.user_link,
        'locale': conf.user_locale,
        'name': conf.user_name,
        'nickname': None,
        'phone': None,
        'picture': conf.user_picture,
        'postal_code': None,
        'timezone': None,
        'username': conf.user_username,
    },
    'content_should_contain': [
        conf.user_id,
        # conf.user_link,
        conf.user_locale,
        conf.user_name,
        conf.user_username,

        # User info JSON keys
        'id', 'id_str', 'name', 'screen_name', 'location', 'profile_location',
        'description', 'url', 'entities', 'urls', 'expanded_url', 'display_url',
        'indices', 'protected', 'followers_count', 'friends_count',
        'listed_count', 'created_at', 'favourites_count', 'utc_offset',
        'time_zone', 'geo_enabled', 'verified', 'statuses_count', 'lang',
        'status', 'text', 'source', 'truncated', 'in_reply_to_status_id',
        'in_reply_to_status_id_str', 'in_reply_to_user_id',
        'in_reply_to_user_id_str', 'in_reply_to_screen_name', 'geo',
        'coordinates', 'place', 'contributors', 'retweeted_status',
        'retweet_count', 'favorite_count', 'hashtags', 'symbols',
        'user_mentions', 'favorited', 'retweeted', 'possibly_sensitive',
        'contributors_enabled', 'is_translator', 'is_translation_enabled',
        'profile_background_color', 'profile_background_image_url',
        'profile_background_image_url_https', 'profile_background_tile',
        'profile_image_url', 'profile_image_url_https', 'profile_link_color',
        'profile_sidebar_border_color', 'profile_sidebar_fill_color',
        'profile_text_color', 'profile_use_background_image', 'default_profile',
        'default_profile_image', 'following', 'follow_request_sent',
        'notifications'
    ],
    # Case insensitive
    'content_should_not_contain':
        conf.no_birth_date +
        conf.no_gender +
        conf.no_nickname +
        conf.no_phone +
        conf.no_postal_code +
        conf.no_timezone,
    # True means that any thruthy value is expected
    'credentials': {
        '_expiration_time': None,
        '_expire_in': True,
        'consumer_key': True,
        'consumer_secret': True,
        'provider_id': None,
        'provider_name': 'twitter',
        'provider_type': 'authomatic.providers.oauth1.OAuth1',
        'provider_type_id': '1-5',
        'refresh_status': constants.CREDENTIALS_REFRESH_NOT_SUPPORTED,
        'refresh_token': None,
        'token': True,
        'token_secret': True,
        'token_type': None,
    },
}