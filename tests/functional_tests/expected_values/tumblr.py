import re

import fixtures
import constants
from authomatic.providers import oauth1


conf = fixtures.get_configuration('tumblr')

CONFIG = {
    'login_xpath': '//*[@id="signup_email"]',
    'password_xpath': '//*[@id="signup_password"]',
    'consent_xpaths': [
        '//*[@id="api_v1_oauth_authorize"]/div[2]/div/div[1]/div/div/div[2]/form/button[2]',
    ],
    'class_': oauth1.Tumblr,
    'user': {
        'birth_date': None,
        'city': None,
        'country': None,
        'email': None,
        'gender': None,
        'id': conf.user_id,
        'first_name': None,
        'last_name': None,
        'link': None,
        'locale': None,
        'location': None,
        'name': conf.user_name,
        'nickname': None,
        'phone': None,
        'picture': None,
        'postal_code': None,
        'timezone': None,
        'username': conf.user_username,
    },
    'content_should_contain': [
        conf.user_id,
        conf.user_name,
        conf.user_username,

        # User info JSON keys
        'admin', 'ask', 'ask_anon', 'ask_page_title', 'blogs',
        'can_send_fan_mail', 'default_post_format', 'description', 'drafts',
        'facebook', 'facebook_opengraph_enabled', 'followed', 'followers',
        'following', 'is_nsfw', 'likes', 'messages', 'meta', 'msg', 'name',
        'posts', 'primary', 'queue', 'response', 'share_likes', 'status',
        'title', 'tweet', 'twitter_enabled', 'twitter_send', 'type', 'updated',
        'url', 'user'
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
        'provider_name': 'tumblr',
        'provider_type': 'authomatic.providers.oauth1.OAuth1',
        'provider_type_id': '1-6',
        'refresh_status': constants.CREDENTIALS_REFRESH_NOT_SUPPORTED,
        'refresh_token': None,
        'token': True,
        'token_secret': True,
        'token_type': None,
    },
}