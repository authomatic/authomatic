from google.appengine.api import urlfetch
from simpleauth2 import Credentials, User, Request, query_string_parser, \
    json_parser, AuthEvent
from urllib import urlencode
import logging
import oauth2 as oauth1


class BaseProvider(object):
    """
    Base class for all providers
    """
     
    def __init__(self, phase, provider_name, consumer, handler, session, session_key, callback):
        self.phase = phase
        self.provider_name = provider_name
        self.consumer = consumer
        self.handler = handler
        self.session = session
        self.session_key = session_key
        self.callback = callback
        self.user = User()        
                
        self._user_info_request = None
                
        self.type = self.__class__.__bases__[0].__name__
        
        # recreate full current URI
        self.uri = handler.uri_for(handler.request.route.name, *handler.request.route_args, _full=True)
    
    
    #=======================================================================
    # Static properties to be overriden by subclasses
    #=======================================================================
    
    # tuple of URLs ordered by their usage
    urls = (None, )
    
    # tuple of callables which parse responses returned by providers ordered by their usage
    parsers = (lambda content: content, )
    
    # Override this property to fix different naming conventions for user info values returned by providers.
    # keys are the names of the User class properties
    # values are either strings specifiing which key of the data dictionary should be used,
    # or callables expecting the data dictionary as argument and returning the desired value
    user_info_mapping = {}
    
    
    #===========================================================================
    # Methods to be overriden by subclasses
    #===========================================================================
        
    def __call__(self):
        pass
    
    
    #===========================================================================
    # Exposed methods
    #===========================================================================
    
    def fetch(self, url, parser=None):
        return self.create_request(url, parser=parser).fetch().get_result()
    
    
    def create_request(self, url, method='GET', parser=None):
        
        return Request(url=url,
                                  credentials=self.credentials,
                                  method=method,
                                  parser=parser)
        
    
    def fetch_user_info(self):
        return self.user_info_request.fetch().get_result()
    
    
    @property
    def user_info_request(self): pass
    
    @user_info_request.getter
    def user_info_request(self):
        if not self._user_info_request:
            def parser(result):
                return self._update_user(result.data)
            parser = lambda result: self._update_user(result.data)
            self._user_info_request = self.create_request(self.urls[-1], parser=parser)
        return self._user_info_request
    
    
    #===========================================================================
    # Internal methods
    #===========================================================================
    
    def _update_user(self, data):
        """
        Updates the properties of the self.user object.
        
        Takes into account the self.user_info_mapping property.
        """
        self.user.raw_user_info = data
        
        # iterate over User properties
        for key in self.user.__dict__.keys():
            # exclude raw_user_info
            if key is not 'raw_user_info':
                
                # check if there is a diferent key in the user_info_mapping
                data_key = self.user_info_mapping.get(key) or key
                
                if type(data_key) is str:
                    # get value from data
                    new_value = data.get(data_key)
                elif callable(data_key):
                    new_value = data_key(data)
                else:
                    raise Exception('The values of the user_info_mapping dict must be a string or callable. {} found under "{}" key.'.format(type(data_key), key))                
                
                # update user
                if new_value:
                    setattr(self.user, key, new_value)
        
        return self.user
    
    
    def _credentials_parser(self, response):
        credentials = Credentials(response.get('access_token'))
        
        credentials.access_token_secret = response.get('access_token_secret')
        credentials.expires_in = response.get('expires_in')
        credentials.provider_type = self.type
        
        return credentials
    
    
    def _save_sessions(self):
        self.session.container.session_store.save_sessions(self.handler.response)
    
    
    def _reset_phase(self):
        #TODO: Check if it would not be better to reset whole session
        self.session.setdefault(self.session_key, {}).setdefault(self.provider_name, {})['phase'] = 0
        self._save_sessions()
    
    
    def _normalize_scope(self, scope):
        """
        Convert scope list to csv
        """
        
        return ','.join(scope) if scope else None


#===============================================================================
# OAuth 2.0
#===============================================================================

class OAuth2(BaseProvider):
    """
    Base class for OAuth2 services
    """
    
    def __call__(self):
        
        if self.phase == 0:
            
            # prepare url parameters
            params = dict(client_id=self.consumer.key,
                          redirect_uri=self.uri,
                          response_type='code',
                          scope=self._normalize_scope(self.consumer.scope))
            
            #  generate CSRF token, save it to storage and add to url parameters
            
            
            # redirect to to provider to get access token
            redirect_url = self.urls[0] + '?' + urlencode(params)
            
            self.handler.redirect(redirect_url)
            
        if self.phase == 1:
            # retrieve CSRF token from storage
            
            # Compare it with state returned by provider
            
            # check access token
            self.consumer.access_token = self.handler.request.get('code')
            if not self.consumer.access_token:
                self._reset_phase()
                raise Exception('Failed to get access token from provider {}!'.format(self.provider_name))
            
            # exchange authorisation code for access token by the provider
            params = dict(code=self.consumer.access_token,
                          client_id=self.consumer.key,
                          client_secret=self.consumer.secret,
                          redirect_uri=self.uri,
                          grant_type='authorization_code')
            
            response = urlfetch.fetch(self.urls[1],
                                      payload=urlencode(params),
                                      method=urlfetch.POST,
                                      headers={'Content-Type': 'application/x-www-form-urlencoded'})
            
            # parse response
            response = self.parsers[1](response.content)
            
            # create user
            self._update_user(response)
            
            # create credentials
            self.credentials = self._credentials_parser(response)
            
            # create event
            event = AuthEvent(self, self.consumer, self.user, self.credentials)
            
            # reset phase
            self._reset_phase()
            
            # call callback with event
            self.callback(event)


class Facebook(OAuth2):
    """
    Facebook Oauth 2.0 service
    """
    
    # class properties
    urls = ('https://www.facebook.com/dialog/oauth',
            'https://graph.facebook.com/oauth/access_token',
            'https://graph.facebook.com/me')
    
    parsers = (None, query_string_parser)
    
    user_info_mapping = dict(user_id='id',
                            picture=(lambda data: 'http://graph.facebook.com/{}/picture?type=large'.format(data.get('username'))))
    
    def _credentials_parser(self, response):
        """
        We need to override this method to fix Facebooks naming deviation
        """
        credentials = super(Facebook, self)._credentials_parser(response)
        
        # Facebook returns "expires" instead of "expires_in"
        credentials.expires_in = response.get('expires')
        return credentials


class Google(OAuth2):
    """
    Google Oauth 2.0 service
    """
    
    # class properties
    urls = ('https://accounts.google.com/o/oauth2/auth',
            'https://accounts.google.com/o/oauth2/token',
            'https://www.googleapis.com/oauth2/v1/userinfo')
    
    parsers = (None, json_parser)
    
    user_info_mapping = dict(name='name',
                            first_name='given_name',
                            last_name='family_name',
                            user_id='id')
    
    def _normalize_scope(self, scope):
        """
        Google has space-separated scopes
        """
        return ' '.join(scope)
    
    
class WindowsLive(OAuth2):
    """
    Windlows Live Oauth 2.0 service
    """
    
    # class properties
    urls = ('https://oauth.live.com/authorize',
            'https://oauth.live.com/token',
            'https://apis.live.net/v5.0/me')
    
    parsers = (None, json_parser)
    
    user_info_mapping=dict(user_id='id',
                           email=(lambda data: data.get('emails', {}).get('preferred')))


#===============================================================================
# Oauth 1.0
#===============================================================================

class OAuth1(BaseProvider):
    def __init__(self, *args, **kwargs):
        super(OAuth1, self).__init__(*args, **kwargs)
        
        # create keys under which oauth token and secret will be stored in session
        self._oauth_token_key = self.provider_name + '_oauth_token'
        self._oauth_token_secret_key = self.provider_name + '_oauth_token_secret'
    
    def _credentials_parser(self, response):
        
        credentials = super(OAuth1, self)._credentials_parser(response)
        
        credentials.access_token = response.get('oauth_token')
        credentials.access_token_secret = response.get('oauth_token_secret')
        
        credentials.consumer_key = self.consumer.key
        credentials.consumer_secret = self.consumer.secret
        credentials.provider_type = self.type        
        
        return credentials    
    
    def __call__(self):
        if self.phase == 0:
            
            # create OAuth 1.0 client
            client = oauth1.Client(oauth1.Consumer(self.consumer.key, self.consumer.secret))
            
            # fetch the client
            response = client.request(self.urls[0], "GET")
            
            # check if response status is OK
            if response[0].get('status') != '200':
                self._reset_phase()
                raise Exception('Could not fetch a valid response from provider {}!'.format(self.provider_name))
            
            # extract OAuth token and save it to session
            oauth_token = self.parsers[0](response[1]).get('oauth_token')
            if not oauth_token:
                self._reset_phase()
                raise Exception('Could not get a valid OAuth token from provider {}!'.format(self.provider_name))
            #self.session[session_key][self._oauth_token_key] = oauth_token
            self.session[self.session_key][self.provider_name]['oauth_token'] = oauth_token
            
            # extract OAuth token secret and save it to session
            oauth_token_secret = self.parsers[0](response[1]).get('oauth_token_secret')
            if not oauth_token_secret:
                self._reset_phase()
                raise Exception('Could not get a valid OAuth token secret from provider {}!'.format(self.provider_name))
            #self.session[session_key][self._oauth_token_secret_key] = oauth_token_secret
            self.session[self.session_key][self.provider_name]['oauth_token_secret'] = oauth_token_secret
            
            # save sessions
            self._save_sessions()
            
            # redirect to request access token from provider
            params = urlencode(dict(oauth_token=oauth_token,
                                    oauth_callback=self.uri))
            self.handler.redirect(self.urls[1] + '?' + params)
        
        if self.phase == 1:
            
            # retrieve the OAuth token from session
            try:
                oauth_token = self.session[self.session_key][self.provider_name]['oauth_token']
            except KeyError:
                self._reset_phase()
                raise Exception('OAuth token could not be retrieved from session!')
            
            try:
                oauth_token_secret = self.session[self.session_key][self.provider_name]['oauth_token_secret']
            except KeyError:
                self._reset_phase()
                raise Exception('OAuth token secret could not be retrieved from session!')
            
            # extract the verifier
            verifier = self.handler.request.get('oauth_verifier')
            if not verifier:
                self._reset_phase()
                raise Exception('No OAuth verifier was returned by the {} provider!'.format(self.provider_name))
            
            # create OAuth 1.0 client
            token = oauth1.Token(oauth_token, oauth_token_secret)
            token.set_verifier(verifier)
            client = oauth1.Client(oauth1.Consumer(self.consumer.key, self.consumer.secret), token)
            
            # fetch response
            response = client.request(self.urls[2], "POST")
            
            # parse response
            response = self.parsers[1](response[1])
            
            logging.info('response = {}'.format(response))
            
            self.user = User(response.get('oauth_token'), response.get('oauth_token_secret'), response.get('user_id'))
            
            self.credentials = self._credentials_parser(response)
            
            # create event
            event = AuthEvent(self, self.consumer, self.user, self.credentials)
            
            # reset phase
            self._reset_phase()
            
            # call callback
            self.callback(event)

class Twitter(OAuth1):
    urls = ('https://api.twitter.com/oauth/request_token',
            'https://api.twitter.com/oauth/authorize',
            'https://api.twitter.com/oauth/access_token',
            'https://api.twitter.com/1/account/verify_credentials.json')
    
    parsers = (query_string_parser, query_string_parser)
    
    user_info_mapping = dict(user_id='id',
                            username='screen_name',
                            picture='profile_image_url',
                            locale='lang',
                            link='url')
    