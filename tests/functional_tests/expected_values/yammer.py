from datetime import datetime

import fixtures
import constants
from authomatic.providers import oauth2

conf = fixtures.get_configuration('yammer')

LINK = 'https://www.yammer.com/peterhudec.com/users/{0}'\
    .format(conf.user_username)

# Yammer allows users to only set month and day of their birth day.
# The year is always 1900.
BD = datetime.strptime(conf.user_birth_date, '%x')
BIRTH_DATE = datetime(1900, BD.month, BD.day).strftime('%x')

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
        'location': conf.user_location,
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
        'absolute_timestamps', 'activated_at', 'address', 'admin',
        'admin_can_delete_messages', 'allow_attachments',
        'allow_external_sharing', 'allow_inline_document_view',
        'allow_inline_video', 'allow_notes', 'allow_yammer_apps', 'birth_date',
        'can_broadcast', 'can_browse_external_networks',
        'can_create_new_network', 'contact', 'department',
        'dismissed_apps_tooltip', 'dismissed_browser_lifecycle_banner',
        'dismissed_feed_tooltip', 'dismissed_group_tooltip',
        'dismissed_invite_tooltip', 'dismissed_invite_tooltip_at',
        'dismissed_profile_prompt', 'email', 'email_addresses', 'enable_chat',
        'enable_groups', 'enable_private_messages',
        'enter_does_not_submit_message', 'expertise', 'external_urls',
        'first_name', 'follow_general_messages', 'followers', 'following',
        'full_name', 'guid', 'has_fake_email', 'has_mobile_client',
        'has_yammer_now', 'id', 'im', 'interests', 'job_title', 'kids_names',
        'last_name', 'locale', 'location', 'make_yammer_homepage',
        'message_prompt', 'mugshot_url', 'mugshot_url_template', 'name',
        'network_domains', 'network_id', 'network_name', 'network_settings',
        'number', 'phone_numbers', 'preferred_my_feed', 'prescribed_my_feed',
        'previous_companies', 'provider', 'schools', 'settings',
        'show_ask_for_photo', 'show_communities_directory', 'significant_other',
        'state', 'stats', 'sticky_my_feed', 'summary', 'threaded_mode',
        'timezone', 'type', 'updates', 'url', 'username', 'verified_admin',
        'web_preferences', 'web_url', 'xdr_proxy', 'yammer_now_app_id'
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