import fixtures
from authomatic.providers import oauth2


conf = fixtures.get_configuration('facebook')

LINK = 'https://www.facebook.com/' + conf.user_username_reverse
PICTURE = 'http://graph.facebook.com/{}/picture?type=large'\
    .format(conf.user_username_reverse)

CONFIG = {
    'class_': oauth2.Facebook,
    'scope': oauth2.Facebook.user_info_scope,
    'fixture': fixtures.providers.FacebookFixture(conf.user_login,
                                                  conf.user_password),
    'user': {
        'id': conf.user_id,
        'email': conf.user_email,
        'username': conf.user_username_reverse,
        'name': conf.user_name,
        'first_name': conf.user_first_name,
        'last_name': conf.user_last_name,
        'nickname': None,
        'birth_date': None,
        'city': conf.user_city,
        'country': conf.user_country,
        'gender': conf.user_gender,
        'link': LINK,
        'locale': conf.user_locale,
        'phone': None,
        'picture': PICTURE,
        'postal_code': None,
        'timezone': conf.user_timezone,
    },
    'content_should_contain': [
        conf.user_id,
        conf.user_username_reverse,
        conf.user_name,
    ],
    # Case insensitive
    'content_should_not_contain': conf.no_phone + conf.no_birth_date,
}