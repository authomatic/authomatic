# encoding: utf-8
from authomatic.providers import oauth2, oauth1
from fixtures import providers

# Host and port where the application shoul listen to
HOST = '127.0.0.1'
PORT = 8080

# You need to alias the host in the /etc/hosts file
# to be able to test some services like Facebook localy
HOST_ALIAS = 'authomatic.com'

LOGIN = 'andypipkin'
EMAIL = 'andy.pipkin@littlebritain.co.uk'
PASSWORD = '##########'

# None values mean that the provider doesn't support the particular property
PROVIDERS = {
    'facebook': {
        'class_': oauth2.Facebook,
        'consumer_key': '##########',
        'consumer_secret': '##########',
        'scope': ['user_about_me', 'email', 'publish_stream'],
        'fixture': providers.FacebookFixture(EMAIL, PASSWORD),
        'user': {
            'id': '##########',
            'email': EMAIL,
            'username': 'andypipkin',
            'name': 'Andy Pipkin',
            'first_name': 'Andy',
            'last_name': 'Pipkin',
            'nickname': None,
            'birth_date': None,
            'city': None,
            'country': None,
            'gender': 'male',
            'link': 'https://www.facebook.com/andypipkin',
            'locale': 'en_US',
            'phone': None,
            'picture': 'http://graph.facebook.com/andypipkin/picture?type=large',
            'postal_code': None,
            'timezone': '1',
        },
        'content_should_contain': [
            '##########', # ID
            'andy.pipkin\u0040littlebritain.co.uk',
            'Andy Pipkin',
        ],
        # Case insensitive
        # TODO: Convert to regular expressions?
        'content_should_not_contain': [
            '##########', # Phone Number
            '1901', # Part of birth_date
            'London', # Test will fail and reveal that Facebook now supports City
            'Great Britain', # Test will fail and reveal that Facebook now supports Country
        ],
    },
}