import fixtures
from authomatic.providers import oauth2


conf = fixtures.get_configuration('deviantart')

PICTURE = 'https://a.deviantart.net/avatars/p/e/{}.jpg?1'\
    .format(conf.user_username)

CONFIG = {
    'class_': oauth2.DeviantART,
    'scope': oauth2.DeviantART.user_info_scope,
    'fixture': fixtures.providers.DeviantART(conf.user_login,
                                             conf.user_password),
    'user': {
        'id': None,
        'email': None,
        'username': conf.user_username,
        'name': conf.user_username,
        'first_name': None,
        'last_name': None,
        'nickname': None,
        'birth_date': None,
        'city': None,
        'country': None,
        'gender': None,
        'link': None,
        'locale': None,
        'phone': None,
        'picture': PICTURE,
        'postal_code': None,
        'timezone': None,
    },
    'content_should_contain': [
        conf.user_username,
    ],
    # Case insensitive
    'content_should_not_contain': conf.no_phone + conf.no_birth_date +
                                  conf.no_email + conf.no_location +
                                  conf.no_gender + conf.no_locale +
                                  conf.no_first_name + conf.no_last_name,
}