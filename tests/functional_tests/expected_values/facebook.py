from datetime import datetime
import re

import fixtures
import constants
from authomatic.providers import oauth2

conf = fixtures.get_configuration('facebook')

# LINK = u'http://www.facebook.com/' + conf.user_id
LINK = u'https://www.facebook.com/{0}'.format(conf.user_id)
PICTURE = (u'http://graph.facebook.com/{0}/picture?type=large'
           .format(conf.user_id))

CONFIG = {
    'login_xpath': u'//*[@id="email"]',
    'password_xpath': u'//*[@id="pass"]',
    'consent_xpaths': [
        '//*[@id="platformDialogForm"]/div[2]/table/tbody/tr/td[2]/button[2]'
    ],
    'after_consent_wait_seconds': 1,
    'class_': oauth2.Facebook,
    'scope': oauth2.Facebook.user_info_scope,
    'user': {
        'birth_date': conf.user_birth_date_str,
        'city': conf.user_city,
        'country': conf.user_country,
        'email': conf.user_email,
        'first_name': conf.user_first_name,
        'gender': conf.user_gender,
        'id': conf.user_id,
        'last_name': conf.user_last_name,
        'link': LINK,
        'locale': conf.user_locale,
        'location': conf.user_location,
        'name': conf.user_name,
        'nickname': None,
        'phone': None,
        'picture': PICTURE,
        'postal_code': None,
        'timezone': re.compile(r'\d'),
        'username': None,
    },
    'content_should_contain': [
        conf.user_birth_date.strftime(u'%m\/%d\/%Y'),
        conf.user_city,
        conf.user_country,
        conf.user_email.replace('@', '\\u0040'),
        conf.user_first_name,
        conf.user_gender,
        conf.user_id,
        conf.user_last_name,
        conf.user_locale,
        conf.user_location,

        # User info JSON keys
        'birthday', 'data', 'email', 'first_name', 'gender', 'id',
        'is_silhouette', 'last_name', 'locale', 'location', 'name', 'picture',
        'timezone', 'url'
    ],
    # Case insensitive
    'content_should_not_contain':
        conf.no_nickname +
        conf.no_phone +
        conf.no_postal_code +
        conf.no_username,
    # True means that any truthy value is expected
    'credentials': {
        'token_type': 'Bearer',
        'provider_type_id': '2-5',
        '_expiration_time': True,
        'consumer_key': None,
        'provider_id': None,
        'consumer_secret': None,
        'token': True,
        'token_secret': None,
        '_expire_in': True,
        'provider_name': 'facebook',
        'refresh_token': None,
        'provider_type': 'authomatic.providers.oauth2.OAuth2',
        'refresh_status': constants.CREDENTIALS_REFRESH_OK,
    },
    # Testing changes after credentials refresh
    # same: True
    # not same: False
    # don't test: None
    'credentials_refresh_change': {
        'token_type': True,
        'provider_type_id': True,
        '_expiration_time': None,
        'consumer_key': True,
        'provider_id': True,
        'consumer_secret': True,
        'token': False,
        'token_secret': True,
        '_expire_in': None,
        'provider_name': True,
        'refresh_token': True,
        'provider_type': True,
    },
}