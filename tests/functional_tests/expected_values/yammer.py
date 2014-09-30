import fixtures
import constants
from authomatic.providers import oauth2

conf = fixtures.get_configuration('yammer')

LINK = 'https://www.yammer.com/peterhudec.com/users/{}'\
    .format(conf.user_username)

# Yammer allows users to only set month and day of their birth day.
# The year is always 1900.
BIRTH_DATE = '1900' + conf.user_birth_date[4:]

CONFIG = {
    'login_xpath': '//*[@id="login"]',
    'password_xpath': '//*[@id="password"]',
    'consent_xpaths': [
        '//*[@id="login-form"]/fieldset[2]/p[2]/button',
        '//*[@id="oauth2-authorize"]/div[3]/div[3]/form/input[1]',
    ],
    'class_': oauth2.Yammer,
    'scope': oauth2.Yammer.user_info_scope,
    'user': {
        'birth_date': BIRTH_DATE,
        'city': conf.user_city,
        'country': conf.user_country,
        'email': conf.user_email,
        'first_name': conf.user_first_name,
        'gender': None,
        'id': conf.user_id,
        'last_name': conf.user_last_name,
        'link': LINK,
        'locale': conf.user_locale,
        'name': conf.user_name,
        'nickname': None,
        'phone': conf.user_phone,
        'picture': conf.user_picture,
        'postal_code': None,
        'timezone': conf.user_timezone,
        'username': conf.user_username,
    },
    'content_should_contain': [
        conf.user_city,
        conf.user_country,
        conf.user_email,
        conf.user_first_name,
        conf.user_id,
        conf.user_last_name,
        LINK,
        conf.user_locale,
        conf.user_name,
        conf.user_phone,
        conf.user_picture,
        conf.user_timezone.replace('&', '\\u0026'),
        conf.user_username,

        # User info JSON keys
        'type', 'id', 'network_id', 'state', 'guid', 'job_title', 'location',
        'significant_other', 'kids_names', 'interests', 'summary', 'expertise',
        'full_name', 'activated_at', 'show_ask_for_photo', 'first_name',
        'last_name', 'network_name', 'network_domains', 'url', 'web_url',
        'name', 'mugshot_url', 'mugshot_url_template', 'hire_date',
        'birth_date', 'timezone', 'external_urls', 'admin', 'verified_admin',
        'can_broadcast', 'department', 'previous_companies', 'schools',
        'contact', 'im', 'provider', 'username', 'phone_numbers', 'number',
        'email_addresses', 'address', 'has_fake_email', 'stats', 'following',
        'followers', 'updates', 'settings', 'xdr_proxy', 'web_preferences',
        'absolute_timestamps', 'threaded_mode', 'network_settings',
        'message_prompt', 'allow_attachments', 'show_communities_directory',
        'enable_groups', 'allow_yammer_apps', 'admin_can_delete_messages',
        'allow_inline_document_view', 'allow_inline_video',
        'enable_private_messages', 'allow_external_sharing', 'enable_chat',
        'home_tabs', 'select_name', 'feed_description', 'ordering_index',
        'enter_does_not_submit_message', 'preferred_my_feed',
        'prescribed_my_feed', 'sticky_my_feed', 'dismissed_feed_tooltip',
        'dismissed_group_tooltip', 'dismissed_profile_prompt',
        'dismissed_invite_tooltip', 'dismissed_apps_tooltip',
        'dismissed_invite_tooltip_at', 'dismissed_browser_lifecycle_banner',
        'make_yammer_homepage', 'locale', 'yammer_now_app_id', 'has_yammer_now',
        'has_mobile_client', 'follow_general_messages'
    ],
    # Case insensitive
    'content_should_not_contain':
        conf.no_gender +
        conf.no_nickname +
        conf.no_postal_code,
    # True means that any thruthy value is expected
    'credentials': {
        'token_type': 'Bearer',
        'provider_type_id': '2-15',
        '_expiration_time': None,
        'consumer_key': None,
        'provider_id': None,
        'consumer_secret': None,
        'token': True,
        'token_secret': None,
        '_expire_in': True,
        'provider_name': 'yammer',
        'refresh_token': None,
        'provider_type': 'authomatic.providers.oauth2.OAuth2',
        'refresh_status': constants.CREDENTIALS_REFRESH_NOT_SUPPORTED,
    },
}