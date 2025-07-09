import re

import fixtures
import constants
from authomatic.providers import oauth1

conf = fixtures.get_configuration('xing')

LINK = f'https://www.xing.com/profile/{conf.user_username}'
PICTURE = re.compile(r'https://www.xing.com/assets/frontend_minified/'
                     r'img/users/\w+\.\d+x\d+.jpg')


CONFIG = {
    'logout_url': 'https://www.xing.com/app/user?op=logout',
    'login_xpath': '//*[@id="login_form_username"]',
    'password_xpath': '//*[@id="login_form_password"]',
    'consent_xpaths': [
        '//*[@id="oauth-container"]/div/div/div/form/input[5]',
    ],
    'consent_wait_seconds': 3,
    'class_': oauth1.Xing,
    'user': {
        'birth_date': conf.user_birth_date_str,
        'city': re.compile(r'^[\w. -]+$'),
        'country': re.compile(r'^\w{2}$'),
        'email': conf.user_email,
        'gender': re.compile(r'^\w$'),
        'id': conf.user_id,
        'first_name': conf.user_first_name,
        'last_name': conf.user_last_name,
        'link': LINK,
        'locale': re.compile(r'^\w{2}$'),
        'location': re.compile(r'^[\w. -]+, \w{2}$'),
        'name': conf.user_name,
        'nickname': None,
        'phone': conf.user_phone,
        'picture': PICTURE,
        'postal_code': conf.user_postal_code,
        'timezone': re.compile(r'^\w+/\w+$'),
        'username': conf.user_username,
    },
    'content_should_contain': [
        f'"year":{conf.user_birth_date:%Y},',
        f'"month":{conf.user_birth_date:%m},',
        f'"day":{conf.user_birth_date:%d}',
        conf.user_email,
        conf.user_first_name,
        conf.user_id,
        conf.user_last_name,
        LINK,
        conf.user_name,
        conf.user_postal_code,
        conf.user_username,

        # User info JSON keys
        'active_email', 'awards', 'badges', 'begin_date', 'birth_date',
        'business_address', 'career_level', 'city', 'companies', 'company_size',
        'country', 'day', 'degree', 'description', 'discipline', 'display_name',
        'educational_background', 'email', 'employment_status', 'en',
        'end_date', 'fax', 'first_name', 'form_of_employment', 'gender',
        'haves', 'id', 'industry', 'instant_messaging_accounts', 'interests',
        'languages', 'large', 'last_name', 'maxi_thumb', 'medium_thumb',
        'mini_thumb', 'mobile_phone', 'month', 'name', 'non_primary_companies',
        'organisation_member', 'page_name', 'permalink', 'phone', 'photo_urls',
        'premium_services', 'primary_company', 'primary_school',
        'private_address', 'professional_experience', 'province',
        'qualifications', 'schools', 'size_1024x1024', 'size_128x128',
        'size_192x192', 'size_256x256', 'size_32x32', 'size_48x48',
        'size_64x64', 'size_96x96', 'size_original', 'street', 'tag', 'thumb',
        'time_zone', 'title', 'until_now', 'url', 'users', 'utc_offset',
        'wants', 'web_profiles', 'year', 'zip_code'
    ],
    # Case insensitive
    'content_should_not_contain':
        conf.no_nickname,
    # True means that any truthy value is expected
    'credentials': {
        '_expiration_time': None,
        '_expire_in': True,
        'consumer_key': True,
        'consumer_secret': True,
        'provider_id': None,
        'provider_name': 'xing',
        'provider_type': 'authomatic.providers.oauth1.OAuth1',
        'provider_type_id': '1-11',
        'refresh_status': constants.CREDENTIALS_REFRESH_NOT_SUPPORTED,
        'refresh_token': None,
        'token': True,
        'token_secret': True,
        'token_type': None,
    },
}
