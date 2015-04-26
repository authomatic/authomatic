import re

import fixtures
import constants
from authomatic.providers import oauth2


conf = fixtures.get_configuration('github')

LINK = 'https://github.com/{0}'.format(conf.user_username)
PICTURE = re.compile(r'https://avatars\.githubusercontent.com/u/{0}\?v=\d'
                     .format(conf.user_id))

CONFIG = {
    'login_xpath': '//*[@id="login_field"]',
    'password_xpath': '//*[@id="password"]',
    'consent_xpaths': [
        '//*[@id="login"]/form/div[3]/input[4]',
        '//*[@id="site-container"]/div/div[2]/form/p/button',
    ],
    'class_': oauth2.GitHub,
    'scope': oauth2.GitHub.user_info_scope,
    'user': {
        'birth_date': None,
        'city': None,
        'country': None,
        'email': conf.user_email,
        'first_name': None,
        'gender': None,
        'id': conf.user_id,
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
        'username': conf.user_username,
    },
    'content_should_contain': [
        conf.user_id,
        conf.user_name, conf.user_first_name, conf.user_last_name,
        conf.user_city, conf.user_country,

        # User info JSON keys
        'login', 'id', 'avatar_url', 'gravatar_id', 'url', 'html_url',
        'followers_url', 'following_url', 'gists_url', 'starred_url',
        'subscriptions_url', 'organizations_url', 'repos_url', 'events_url',
        'received_events_url', 'type', 'site_admin', 'name', 'company', 'blog',
        'location', 'email', 'hireable', 'bio', 'public_repos', 'public_gists',
        'followers', 'following', 'created_at', 'updated_at'
    ],
    # Case insensitive
    'content_should_not_contain': conf.no_phone + conf.no_birth_date +
                                  conf.no_locale + conf.no_first_name +
                                  conf.no_last_name + conf.no_timezone +
                                  conf.no_gender + conf.no_postal_code +
                                  [conf.user_nickname],
    # True means that any thruthy value is expected
    'credentials': {
        'token_type': 'Bearer',
        'provider_type_id': '2-7',
        '_expiration_time': None,
        'consumer_key': None,
        'provider_id': None,
        'consumer_secret': None,
        'token': True,
        'token_secret': None,
        '_expire_in': True,
        'provider_name': 'github',
        'refresh_token': None,
        'provider_type': 'authomatic.providers.oauth2.OAuth2',
        'refresh_status': constants.CREDENTIALS_REFRESH_NOT_SUPPORTED,
    },
}