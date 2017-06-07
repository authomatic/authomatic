import re


import fixtures
import constants
from authomatic.providers import oauth1

conf = fixtures.get_configuration('plurk')

LINK = 'https://www.plurk.com/{0}/'.format(conf.user_username)
PICTURE = 'https://avatars.plurk.com/{0}-big2.jpg'.format(conf.user_id)

CONFIG = {
    'login_xpath': '//*[@id="input_nick_name"]',
    'password_xpath': '//*[@id="password"]/input',
    'consent_xpaths': [
        '//*[@id="display_board"]/div[2]/div/form/input[5]',
    ],
    'consent_wait_seconds': 5,
    'class_': oauth1.Plurk,
    'user': {
        'birth_date': conf.user_birth_date_str,
        'city': conf.user_city,
        'country': conf.user_country,
        'email': conf.user_email,
        'gender': re.compile(r'^\d$'),
        'id': conf.user_id,
        'first_name': None,
        'last_name': None,
        'link': LINK,
        'locale': re.compile(r'^\w{2}$'),
        'location': conf.user_location,
        'name': conf.user_name,
        'nickname': conf.user_nickname,
        'phone': None,
        'picture': PICTURE,
        'postal_code': None,
        'timezone': 'UTC',
        'username': conf.user_username,
    },
    'content_should_contain': [
        conf.user_birth_date.strftime('%a, %d %b %Y 00:01:00 GMT'),
        conf.user_city,
        conf.user_country,
        conf.user_email,
        conf.user_id,
        conf.user_location,
        conf.user_name,
        conf.user_nickname,
        PICTURE.replace('/', r'\/'),
        conf.user_username,

        # User info JSON keys
        'about', 'accept_private_plurk_from', 'alerts_count', 'anonymous',
        'avatar', 'avatar_big', 'avatar_medium', 'avatar_small',
        'background_id', 'bday_privacy', 'coins', 'content', 'content_raw',
        'creature_url', 'date_of_birth', 'dateformat', 'default_lang',
        'display_name', 'email', 'email_confirmed', 'excluded', 'fans_count',
        'favorers', 'favorite', 'favorite_count', 'friends_count', 'full_name',
        'gender', 'has_gift', 'has_profile_image', 'has_read_permission', 'id',
        'is_unread', 'karma', 'lang', 'last_edited', 'limited_to',
        'link_facebook', 'location', 'mentioned', 'name_color', 'nick_name',
        'no_comments', 'owner_id', 'page_title', 'plurk_id', 'plurk_type',
        'plurks', 'plurks_count', 'plurks_users', 'porn',
        'post_anonymous_plurk', 'posted', 'premium', 'privacy', 'profile_views',
        'qualifier', 'qualifier_translated', 'recruited', 'relationship',
        'replurkable', 'replurked', 'replurker_id', 'replurkers',
        'replurkers_count', 'responded', 'response_count', 'responses_seen',
        'setup_facebook_sync', 'setup_twitter_sync', 'setup_weibo_sync',
        'show_ads', 'show_location', 'timeline_privacy', 'timezone', 'uid',
        'unread_count', 'user_id', 'user_info', 'verified_account'
    ],
    # Case insensitive
    'content_should_not_contain':
        conf.no_first_name +
        conf.no_last_name +
        conf.no_postal_code,
    # True means that any thruthy value is expected
    'credentials': {
        '_expiration_time': None,
        '_expire_in': True,
        'consumer_key': True,
        'consumer_secret': True,
        'provider_id': None,
        'provider_name': 'plurk',
        'provider_type': 'authomatic.providers.oauth1.OAuth1',
        'provider_type_id': '1-4',
        'refresh_status': constants.CREDENTIALS_REFRESH_NOT_SUPPORTED,
        'refresh_token': None,
        'token': True,
        'token_secret': True,
        'token_type': None,
    },
}