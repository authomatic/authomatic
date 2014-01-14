# encoding: utf-8
from authomatic.providers import oauth2, oauth1
from fixtures import providers

LOGIN = 'andypipkin'
EMAIL = 'andypipkin@littlebritain.co.uk'
PASSWORD = '##########'


CONFIG = {
    'facebook': {
        'class_': oauth2.Facebook,
        'consumer_key': '##########',
        'consumer_secret': '##########',
        'scope': ['user_about_me', 'email', 'publish_stream'],
        'fixture': providers.FacebookFixture(EMAIL, PASSWORD),
        'user': {
            'name': 'Andy Pipkin',
            'id': '##########',
        }
    },
}