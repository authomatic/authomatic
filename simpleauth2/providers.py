from urllib import urlencode
import oauth2 as oauth1

from google.appengine.api import urlfetch

from simpleauth2 import Credentials, User, FetchRequest, query_string_parser, json_parser, UserInfo, AuthEvent

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
        
        self.user = None
        
        
        self._user_info_request = None
                
        self.type = self.__class__.__bases__[0].__name__
        
        # recreate full current URI
        self.uri = handler.uri_for(handler.request.route.name, *handler.request.route_args, _full=True)
        
    #=======================================================================
    # Static properties to be overriden by subclasses
    #=======================================================================
    
    # tuple of URLs ordered by their usage
    urls = (None, None)
    
    # tuple of callables which parse responses returned by providers ordered by their usage
    parsers = (lambda content: content, )
    
    #===========================================================================
    # Methods to be overriden by subclasses
    #===========================================================================
    
    def fetch(self, url, parser=None):
        return self.create_request(url, parser=parser).fetch().get_result()
    
    def __call__(self):
        pass
    
    def create_request(self, url, method='GET', parser=None):
        
        return FetchRequest(url=url,
                                  credentials=self.credentials,
                                  method=method,
                                  parser=parser)
        
    def fetch_user_info(self):
        return self.user_info_request.fetch().get_result()
    
    @property
    def user_info_request(self):
        pass
    
    @user_info_request.getter
    def user_info_request(self):
        if not self._user_info_request:
            def parser(result):
                return self.user_info_parser(result.data)
            parser = lambda result: self.user_info_parser(result.data)
            self._user_info_request = self.create_request(self.urls[-1], parser=parser)
        return self._user_info_request
    
    @staticmethod
    def user_info_parser(raw_user_info):
        user_info = UserInfo()
        user_info.raw_user_info = raw_user_info
        return user_info
    
    def _save_sessions(self):
        self.session.container.session_store.save_sessions(self.handler.response)
    
    def _reset_phase(self):
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
    
    @staticmethod
    def user_info_parser(raw_user_info):
        user_info = BaseProvider.user_info_parser(raw_user_info)
        
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
            
            # get access token
            access_token = response.get('access_token')
            
            # create user
            self.user = User(access_token)
            
            # create credentials
            # OAuth 2.0 requires only access token
            self.credentials = Credentials(access_token, expires=response.get('expires'), provider_type=self.type)
            
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
    
class Google(OAuth2):
    """
    Google Oauth 2.0 service
    """
    
    # class properties
    urls = ('https://accounts.google.com/o/oauth2/auth',
            'https://accounts.google.com/o/oauth2/token',
            'https://www.googleapis.com/oauth2/v1/userinfo')
    
    parsers = (None, json_parser)
    
    def _normalize_scope(self, scope):
        """
        Google has space-separated scopes
        """
        return ' '.join(scope)
    
    @staticmethod
    def user_info_parser(raw_user_info):
        user_info = BaseProvider.user_info_parser(raw_user_info)
        
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
    
    parsers = (None, json_parser)
    
    @staticmethod
    def user_info_parser(raw_user_info):
        user_info = BaseProvider.user_info_parser(raw_user_info)
        
        user_info.username = user_info.raw_user_info.get('emails').get('account')
        user_info.username = user_info.raw_user_info.get('emails').get('preferred')
        
        return user_info


#===============================================================================
# Oauth 1.0
#===============================================================================

class OAuth1(BaseProvider):
    def __init__(self, *args, **kwargs):
        super(OAuth1, self).__init__(*args, **kwargs)
        
        # create keys under which oauth token and secret will be stored in session
        self._oauth_token_key = self.provider_name + '_oauth_token'
        self._oauth_token_secret_key = self.provider_name + '_oauth_token_secret'
    
    @staticmethod
    def user_info_parser(raw_user_info):
        user_info = BaseProvider.user_info_parser(raw_user_info)
        
        user_info.raw_user_info = raw_user_info
        user_info.username = raw_user_info.get('screen_name')
        user_info.picture = raw_user_info.get('profile_image_url')
        user_info.name = raw_user_info.get('name')
        user_info.locale = raw_user_info.get('lang')
        user_info.link = raw_user_info.get('url')
        user_info.id = raw_user_info.get('id')
        
        return user_info
    
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
            
            # get access token
            self.access_token = response.get('oauth_token')
            
            # get access token secret
            self.access_token_secret = response.get('oauth_token_secret')
            
            self.user = User(self.access_token, self.access_token_secret)
            
            self.credentials = Credentials(access_token=self.access_token,
                                           access_token_secret=self.access_token_secret,
                                           consumer_key=self.consumer.key,
                                           consumer_secret=self.consumer.secret,
                                           provider_type=self.type)
            
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
    