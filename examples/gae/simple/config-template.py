# config.py

from authomatic.providers import oauth2, oauth1, openid, gaeopenid

CONFIG = {
    'tw': { # Your internal provider name
           
           # Provider class
           'class_': oauth1.Twitter,
           
           # Twitter is an AuthorisationProvider so we need to set several other properties:
           'consumer_key': '##########',
           'consumer_secret': '##########',
    },
    
    # Facebook
    'fb': {
           
           'class_': oauth2.Facebook,
           
           # Facebook is an AuthorisationProvider too.
           'consumer_key': '##########',
           'consumer_secret': '##########',
           
           # But it is also an OAuth 2.0 provider and it needs scope.
           'scope': ['user_about_me', 'email', 'publish_stream']
    },
    
    'gae_oi': {
           
           # OpenID based Google App Engine Users API works only on GAE
           # and returns only the id and email of a user.
           # Moreover, the id is not available in the development environment!
           'class_': gaeopenid.GAEOpenID,
    },
    
    'oi': {
           
           # OpenID based on python-openid library works everywhere,
           # is flexible, but requires more resources.
           'class_': openid.OpenID,
    }
}