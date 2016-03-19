import re

from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.common.keys import Keys

import fixtures
import constants
from authomatic.providers import oauth1

conf = fixtures.get_configuration('twitter')


def after_login_hook(browser, log):
    try:
        log(4, 'twitter', 'Finding challenge element')
        challenge = browser.find_element_by_xpath('//*[@id="challenge_response"]')

        log(4, 'twitter', 'Answering challenge')
        challenge.send_keys(conf.user_challenge_answer)

        log(4, 'twitter', 'Submitting challenge')
        challenge.send_keys(Keys.ENTER)
    except NoSuchElementException:
        log(5, 'twitter', 'Challenge element not found, hopefully not needed')


CONFIG = {
    'login_xpath': '//*[@id="username_or_email"]',
    'password_xpath': '//*[@id="password"]',
    'consent_xpaths': [],
    'after_login_hook': after_login_hook,
    'class_': oauth1.Twitter,
    'user': {
        'birth_date': None,
        'city': None,
        'country': None,
        'email': None,
        'gender': None,
        'id': conf.user_id,
        'first_name': None,
        'last_name': None,
        'link': re.compile(r'^http://t.co/\w+$'),
        'locale': re.compile(r'^\w{2}$'),
        'location': conf.user_location,
        'name': conf.user_name,
        'nickname': None,
        'phone': None,
        'picture': re.compile(r'^http://\w+\.twimg\.com/profile_images/\d+/\w+.jpg$'),
        'postal_code': None,
        'timezone': None,
        'username': conf.user_username,
    },
    'content_should_contain': [
        conf.user_id,
        # conf.user_locale,
        conf.user_name,
        conf.user_username,

        # User info JSON keys
        'contributors', 'contributors_enabled', 'coordinates', 'created_at',
        'default_profile', 'default_profile_image', 'description',
        'display_url', 'entities', 'expanded_url', 'favorite_count',
        'favorited', 'favourites_count', 'follow_request_sent',
        'followers_count', 'following', 'friends_count', 'geo', 'geo_enabled',
        'hashtags', 'id', 'id_str', 'in_reply_to_screen_name',
        'in_reply_to_status_id', 'in_reply_to_status_id_str',
        'in_reply_to_user_id', 'in_reply_to_user_id_str', 'indices',
        'is_translation_enabled', 'is_translator', 'lang', 'listed_count',
        'location', 'name', 'notifications', 'place',
        'profile_background_color', 'profile_background_image_url',
        'profile_background_image_url_https', 'profile_background_tile',
        'profile_image_url', 'profile_image_url_https', 'profile_link_color',
        'profile_sidebar_border_color', 'profile_sidebar_fill_color',
        'profile_text_color', 'profile_use_background_image', 'protected',
        'retweet_count', 'retweeted', 'screen_name', 'source', 'status',
        'statuses_count', 'symbols', 'text', 'time_zone', 'truncated', 'url',
        'urls', 'user_mentions', 'utc_offset', 'verified'
    ],
    # Case insensitive
    'content_should_not_contain':
        conf.no_birth_date +
        conf.no_gender +
        conf.no_nickname +
        # conf.no_phone +  # Contains unrelated phone string
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