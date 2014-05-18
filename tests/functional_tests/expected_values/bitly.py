import fixtures
import constants
from authomatic.providers import oauth2


conf = fixtures.get_configuration('bitly')

LINK = 'http://bitly.com/u/{0}'.format(conf.user_id)
PICTURE = 'http://bitly.com/u/{0}.png'.format(conf.user_id)

CONFIG = {
    'pre_login_xpaths': [
        '//*[@id="oauth_access"]/form/div/div[1]/a',
    ],
    'login_xpath': '//*[@id="username"]',
    'password_xpath': '//*[@id="password"]',
    'consent_xpaths': [
        '//*[@id="oauth_access"]/form/button[1]',
    ],
    'class_': oauth2.Bitly,
    'scope': oauth2.Bitly.user_info_scope,
    'user': {
        'id': conf.user_id,
        'email': None,
        'username': conf.user_username_reverse,
        'name': conf.user_name,
        'first_name': None,
        'last_name': None,
        'nickname': None,
        'birth_date': None,
        'city': None,
        'country': None,
        'gender': None,
        'link': LINK,
        'locale': None,
        'phone': None,
        'picture': PICTURE,
        'postal_code': None,
        'timezone': None,
    },
    'content_should_contain': [
        conf.user_id,
        conf.user_username_reverse,
        conf.user_name,

        # User info JSON keys
        'status_code', 'data', 'apiKey', 'domain_options', 'member_since',
        'enterprise_permissions', 'has_master', 'profile_image',
        'share_accounts', 'numeric_id', 'account_login', 'account_type',
        'account_id', 'primary', 'visible', 'is_delegated', 'auto_import_links',
        'full_name', 'account_name', 'is_enterprise', 'tracking_domains',
        'default_link_privacy', 'display_name', 'custom_short_domain', 'login',
        'is_verified', 'profile_url', 'status_txt',
    ],
    # Case insensitive
    'content_should_not_contain': conf.no_phone + conf.no_birth_date +
                                  conf.no_email + conf.no_location +
                                  conf.no_gender + conf.no_locale +
                                  conf.no_first_name + conf.no_last_name,
    # True means that any thruthy value is expected
    'credentials': {
        'token_type': None,
        'provider_type_id': '2-2',
        '_expiration_time': None,
        'consumer_key': None,
        'provider_id': None,
        'consumer_secret': None,
        'token': True,
        'token_secret': None,
        '_expire_in': True,
        'provider_name': 'bitly',
        'refresh_token': None,
        'provider_type': 'authomatic.providers.oauth2.OAuth2',
        'refresh_status': constants.CREDENTIALS_REFRESH_NOT_SUPPORTED,
    },
}