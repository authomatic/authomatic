import fixtures
from authomatic.providers import oauth2


conf = fixtures.get_configuration('bitly')

LINK = 'http://bitly.com/u/{}'.format(conf.user_id)
PICTURE = 'http://bitly.com/u/{}.png'.format(conf.user_id)

CONFIG = {
    'class_': oauth2.Bitly,
    'scope': oauth2.Bitly.user_info_scope,
    'fixture': fixtures.providers.BitlyFixture(conf.user_login,
                                               conf.user_password),
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
    ],
    # Case insensitive
    'content_should_not_contain': conf.no_phone + conf.no_birth_date +
                                  conf.no_email + conf.no_location +
                                  conf.no_gender + conf.no_locale +
                                  conf.no_first_name + conf.no_last_name,
}