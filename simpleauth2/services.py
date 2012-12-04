from google.appengine.api import urlfetch
from simpleauth2 import utils
from urllib import urlencode
from utils import json
import logging
import oauth2 as oauth1


class AuthEvent(object):
    def __init__(self, service, access_token=None, expires=None, access_token_secret=None):
        self.service = service
        self.access_token = access_token
        self.expires = expires
    
    def fetch(self, url):
        return self.service.fetch(url)
    
    def get_user_info(self):
        return self.service.get_user_info()

class UserInfo(object):
    def __init__(self, *args, **kwargs):
        self.raw_user_info = kwargs.get('raw_user_info')
        self.ID = kwargs.get('id')
        self.username = kwargs.get('username')
        self.name = kwargs.get('name')
        self.first_name = kwargs.get('first_name')
        self.last_name = kwargs.get('last_name')
        self.link = kwargs.get('link')
        self.gender = kwargs.get('gender')
        self.timezone = kwargs.get('timezone')
        self.locale = kwargs.get('locale')
        self.email = kwargs.get('email')
        self.picture = kwargs.get('picture')

class BaseService(object):
    """
    Base class for all services
    """
        
    def __init__(self, service_name, simpleauth2):
        self.service_name = service_name
        self.simpleauth2 = simpleauth2
        
        self.access_token = None
        self.access_token_secret = None
        
        self.type = self.__class__.__bases__[0].__name__
    
    #=======================================================================
    # Static properties to be overriden by subclasses
    #=======================================================================
    
    # tuple of URLs ordered by their usage
    urls = (None, None)
    
    # tuple of callables which parse responses returned by providers ordered by their usage
    utils = (lambda content: content, )
    
    #===========================================================================
    # Methods to be overriden by subclasses
    #===========================================================================
    
    def fetch(self, url):
        return utils.fetch(self.type,
                           url,
                           self.access_token,
                           self.access_token_secret,
                           self.simpleauth2.service_ID,
                           self.simpleauth2.secret)
    
    def __call__(self):
        pass
    
    def _fetch(self):
        pass
    
    def get_user_info(self):
        pass


#===============================================================================
# OAuth 2.0
#===============================================================================

class OAuth2(BaseService):
    """
    Base class for OAuth2 services
    """
    
    def get_user_info(self):
        
        raw_user_info = self.fetch(self.urls[2])
        
        user_info = UserInfo()
        
        user_info.raw_user_info = raw_user_info
        user_info.id = raw_user_info.get('id')
        user_info.username = user_info.raw_user_info.get('username')
        user_info.locale = raw_user_info.get('locale')
        user_info.gender = raw_user_info.get('gender')
        user_info.link = raw_user_info.get('link')
        user_info.name = user_info.raw_user_info.get('name')
        user_info.first_name = user_info.raw_user_info.get('first_name')
        user_info.last_name = user_info.raw_user_info.get('last_name')
        user_info.timezone = user_info.raw_user_info.get('timezone')
        user_info.email = user_info.raw_user_info.get('email')
        
        return user_info
    
    def __call__(self):
        
        if self.simpleauth2.phase == 0:
            
            # prepare url parameters
            params = dict(client_id=self.simpleauth2.service_ID,
                          redirect_uri=self.simpleauth2.uri,
                          response_type='code',
                          scope=self.simpleauth2.scope)
            
            #  generate CSRF token, save it to storage and add to url parameters
            
            
            # redirect to request access token from provider
            redirect_url = self.urls[0] + '?' + urlencode(params)
            
            self.simpleauth2._handler.redirect(redirect_url)
            
        if self.simpleauth2.phase == 1:
            
            # retrieve CSRF token from storage
            
            # Compare it with state returned by provider
            
            # exchange authorisation code for access token by the provider
            params = dict(code=self.simpleauth2._handler.request.get('code'),
                          client_id=self.simpleauth2.service_ID,
                          client_secret=self.simpleauth2.secret,
                          redirect_uri=self.simpleauth2.uri,
                          grant_type='authorization_code')
            
            response = urlfetch.fetch(self.urls[1],
                                      payload=urlencode(params),
                                      method=urlfetch.POST,
                                      headers={'Content-Type': 'application/x-www-form-urlencoded'})
            
            # parse response
            response = self.utils[1](response.content)
            
            # get access token
            self.access_token = response.get('access_token')
            
            # create event
            event = AuthEvent(self, self.access_token, response.get('expires'))
            
            # call callback
            self.simpleauth2._callback(event)

class Facebook(OAuth2):
    """
    Facebook Oauth 2.0 service
    """
    
    # class properties
    urls = ('https://www.facebook.com/dialog/oauth',
            'https://graph.facebook.com/oauth/access_token',
            'https://graph.facebook.com/me')
    
    utils = (None,
               utils.query_string_parser)
    
class Google(OAuth2):
    """
    Google Oauth 2.0 service
    """
    
    # class properties
    urls = ('https://accounts.google.com/o/oauth2/auth',
            'https://accounts.google.com/o/oauth2/token',
            'https://www.googleapis.com/oauth2/v1/userinfo')
    
    utils = (None,
               utils.json_parser)
    
    def get_user_info(self):
        """
        Overrides the OAuth2.get_user_info() method to fix Google's different naming conventions
        """
        user_info = OAuth2.get_user_info(self)
        
        user_info.name = user_info.raw_user_info.get('name')
        user_info.first_name = user_info.raw_user_info.get('given_name')
        user_info.last_name = user_info.raw_user_info.get('family_name')
        user_info.timezone = user_info.raw_user_info.get('timezone')
        user_info.email = user_info.raw_user_info.get('email')
        user_info.picture = user_info.raw_user_info.get('picture')
        
        return user_info
    
class WindowsLive(OAuth2):
    """
    Windlows Live Oauth 2.0 service
    """
    
    # class properties
    urls = ('https://oauth.live.com/authorize',
            'https://oauth.live.com/token',
            'https://apis.live.net/v5.0/me')
    
    utils = (None,
               utils.json_parser)
    
    def get_user_info(self):
        """
        Overrides the OAuth2.get_user_info() method to fix Google's different naming conventions
        """
        user_info = OAuth2.get_user_info(self)
        
        user_info.username = user_info.raw_user_info.get('emails').get('account')
        user_info.username = user_info.raw_user_info.get('emails').get('preferred')
        
        return user_info


#===============================================================================
# Oauth 1.0
#===============================================================================

class OAuth1(BaseService):
    def __init__(self, *args, **kwargs):
        super(OAuth1, self).__init__(*args, **kwargs)
        self._oauth_token_key = self.simpleauth2.service_name + '_oauth_token'
        self._oauth_token_secret_key = self.simpleauth2.service_name + '_oauth_token_secret'
    
    def get_user_info(self):
        
#        token = oauth1.Token(self.access_token, self.access_token_secret)
#        consumer = oauth1.Consumer(self.simpleauth2.service_ID, self.simpleauth2.secret)
#        client = oauth1.Client(consumer,token)
#        
#        response, content = client.request(self.urls[3])
#        
#        raw_user_info = json.loads(content)
#        
        raw_user_info = self.fetch(self.urls[3])
        
        user_info = UserInfo()
        user_info.raw_user_info = raw_user_info
        user_info.username = raw_user_info.get('screen_name')
        user_info.picture = raw_user_info.get('profile_image_url')
        user_info.name = raw_user_info.get('name')
        user_info.locale = raw_user_info.get('lang')
        user_info.link = raw_user_info.get('url')
        user_info.id = raw_user_info.get('id')
        
        return user_info
    
    def __call__(self):
        if self.simpleauth2.phase == 0:
            
            # create OAuth 1.0 client
            client = oauth1.Client(oauth1.Consumer(self.simpleauth2.service_ID, self.simpleauth2.secret))
            
            # fetch the client
            response = client.request(self.urls[0], "GET")
            
            # check if response status is OK
            if response[0].get('status') != '200':
                raise Exception('Could not fetch a valid response from provider {}!'.format(self.service_name))
            
            # extract OAuth token and save it to session
            oauth_token = self.utils[0](response[1]).get('oauth_token')
            if not oauth_token:
                raise Exception('Could not get a valid OAuth token from provider {}!'.format(self.service_name))
            self.simpleauth2._session[self._oauth_token_key] = oauth_token
            
            # extract OAuth token secret and save it to session
            oauth_token_secret = self.utils[0](response[1]).get('oauth_token_secret')
            if not oauth_token_secret:
                raise Exception('Could not get a valid OAuth token secret from provider {}!'.format(self.service_name))
            self.simpleauth2._session[self._oauth_token_secret_key] = oauth_token_secret
            
            # save sessions
            self.simpleauth2._save_sessions()
            
            # redirect to request access token from provider
            params = urlencode(dict(oauth_token=oauth_token,
                                    oauth_callback=self.simpleauth2.uri))
            self.simpleauth2._handler.redirect(self.urls[1] + '?' + params)
        
        if self.simpleauth2.phase == 1:
            
            # retrieve the OAuth token from session
            oauth_token = self.simpleauth2._session.get(self._oauth_token_key)
            if not oauth_token:
                raise Exception('OAuth token could not be retrieved from session!')
            
            # retrieve the OAuth token secret from session
            oauth_token_secret = self.simpleauth2._session.get(self._oauth_token_secret_key)
            if not oauth_token_secret:
                raise Exception('OAuth token secret could not be retrieved from session!')
            
            # extract the verifier
            verifier = self.simpleauth2._handler.request.get('oauth_verifier')
            if not verifier:
                raise Exception('No OAuth verifier was provided by the {} provider!'.format(self.service_name))
            
            # create OAuth 1.0 client
            token = oauth1.Token(oauth_token, oauth_token_secret)
            token.set_verifier(verifier)
            client = oauth1.Client(oauth1.Consumer(self.simpleauth2.service_ID, self.simpleauth2.secret), token)
            
            # fetch response
            response = client.request(self.urls[2], "POST")
            
            # parse response
            response = self.utils[1](response[1])
            
            # get access token
            self.access_token = response.get('oauth_token')
            
            # get access token secret
            self.access_token_secret = response.get('oauth_token_secret')
            
            # create event
            event = AuthEvent(self, self.access_token, access_token_secret=self.access_token_secret)
            
            # call callback
            self.simpleauth2._callback(event)

class Twitter(OAuth1):
    urls = ('https://api.twitter.com/oauth/request_token',
            'https://api.twitter.com/oauth/authorize',
            'https://api.twitter.com/oauth/access_token',
            'https://api.twitter.com/1/account/verify_credentials.json')
    
    utils = (utils.query_string_parser,
               utils.query_string_parser)
    