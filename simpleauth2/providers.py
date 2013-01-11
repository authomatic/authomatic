import simpleauth2
from simpleauth2.exceptions import OAuth2Error
from urllib import urlencode
import logging
import oauth2

QUERY_STRING_PARSER = 'query_string_parser'
JSON_PARSER = 'json_parser'

class BaseProvider(object):
    """
    Base class for all providers
    """
     
    def __init__(self, adapter, phase, provider_name, consumer, callback, provider_id=None):
        self.phase = phase
        self.provider_name = provider_name
        self.consumer = consumer
        self.callback = callback
        self.adapter = adapter
        self.id = provider_id
        
        self.user = None
                
        self._user_info_request = None
                
        self.type = self.__class__.__bases__[0].__name__
        
        # recreate full current URL
        self.uri = self.adapter.get_current_uri()
    
    
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
        
    def login(self):
        pass
    
    
    #===========================================================================
    # Exposed methods
    #===========================================================================
    
    def fetch(self, url, parser=None):
        return self.create_request(url, parser=parser).fetch().get_response()
    
    
    def create_request(self, url, method='GET', content_parser=None, response_parser=None):        
        return simpleauth2.Request(adapter=self.adapter,
                       url=url,
                       credentials=self.credentials,
                       method=method,
                       content_parser=content_parser,
                       response_parser=response_parser)
        
    
    def fetch_user_info(self):
        return self.user_info_request.fetch().get_response()
    
    
    @property
    def user_info_request(self):
        if not self._user_info_request:
            
            def response_parser(response, content_parser):
                response = self.adapter.response_parser(response, content_parser)
                user = self._update_or_create_user(response.data)
                return simpleauth2.UserInfoResponse(response, user)
            
            self._user_info_request = self.create_request(self.urls[-1],
                                                          content_parser=self.adapter.json_parser,
                                                          response_parser=response_parser)
        
        return self._user_info_request
    
    
    #===========================================================================
    # Internal methods
    #===========================================================================
        
    def _fetch(self, content_parser, url, params={}, method='GET', headers={}):
        #TODO: Check whether the method is valid
        
        return self.adapter.fetch_async(content_parser, url, params, method, headers).get_response()
    
    def _update_or_create_user(self, data):
        """
        Updates the properties of the self.user object.
        
        Takes into account the self.user_info_mapping property.
        """
        
        if not self.user:
            self.user = simpleauth2.User()
        
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
    
    
    def _update_credentials(self, data):
        
        self.credentials.access_token_secret = data.get('access_token_secret')
        self.credentials.expires_in = data.get('expires_in')
        
        return self.credentials
        
    
    def _normalize_scope(self, scope):
        """
        Convert scope list to csv
        """
        
        return ','.join(scope) if scope else None
        
    
    def _get_parser_by_index(self, index):
        return getattr(self.adapter, self.parsers[index])


#===============================================================================
# OAuth 2.0
#===============================================================================

class OAuth2(BaseProvider):
    """
    Base class for OAuth2 services
    """
        
    def login(self):
        
        if self.phase == 0:
            
            url = simpleauth2.create_oauth2_url(1, self.urls[0],
                                    consumer_key=self.consumer.key,
                                    redirect_uri=self.uri,
                                    scope=self._normalize_scope(self.consumer.scope))
            
            self.adapter.redirect(url)
            
        if self.phase == 1:
            # retrieve CSRF token from storage
            
            # Compare it with state returned by provider
            
            # check access token
            self.consumer.access_token = self.adapter.get_request_param('code')
            if not self.consumer.access_token:
                self.adapter.reset_phase(self.provider_name)
                raise Exception('Failed to get access token from provider {}!'.format(self.provider_name))
            
            # exchange authorisation code for access token by the provider
            # the parameters should be encoded in the headers so create_oauth2_url() doesn't help
            params = dict(code=self.consumer.access_token,
                          client_id=self.consumer.key,
                          client_secret=self.consumer.secret,
                          redirect_uri=self.uri,
                          grant_type='authorization_code')
            
            parser = self._get_parser_by_index(1)
            response = self._fetch(parser, self.urls[1], params, 'POST', headers={'Content-Type': 'application/x-www-form-urlencoded'})
                        
            # create user
            self._update_or_create_user(response.data)
            
            # create credentials
            self.credentials = simpleauth2.Credentials(response.data.get('access_token'), self.type, self.id)
            self._update_credentials(response.data)
            
            # create event
            event = simpleauth2.AuthEvent(self, self.consumer, self.user, self.credentials)
            
            # reset phase
            self.adapter.reset_phase(self.provider_name)
            
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
    
    parsers = (None, QUERY_STRING_PARSER)
    
    user_info_mapping = dict(user_id='id',
                            picture=(lambda data: 'http://graph.facebook.com/{}/picture?type=large'.format(data.get('username'))))
    
    def _update_credentials(self, data):
        """
        We need to override this method to fix Facebooks naming deviation
        """
        credentials = super(Facebook, self)._update_credentials(data)
        
        # Facebook returns "expires" instead of "expires_in"
        credentials.expires_in = data.get('expires')
        return credentials


class Google(OAuth2):
    """
    Google Oauth 2.0 service
    """
    
    # class properties
    urls = ('https://accounts.google.com/o/oauth2/auth',
            'https://accounts.google.com/o/oauth2/token',
            'https://www.googleapis.com/oauth2/v1/userinfo')
    
    parsers = (None, JSON_PARSER)
    
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
    
    parsers = (None, JSON_PARSER)
    
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
    
    def _update_credentials(self, response):
        
        credentials = super(OAuth1, self)._update_credentials(response)
        
        credentials.access_token = response.get('oauth_token')
        credentials.access_token_secret = response.get('oauth_token_secret')
        
        credentials.consumer_key = self.consumer.key
        credentials.consumer_secret = self.consumer.secret
        credentials.provider_type = self.type        
        
        return credentials    
    
    def login(self):
        if self.phase == 0:
            
            parser = self._get_parser_by_index(0)
            
            # Create Request Token URL
            url1 = simpleauth2.create_oauth1_url(url_type=1,
                                     base=self.urls[0],
                                     consumer_key=self.consumer.key,
                                     consumer_secret=self.consumer.secret,
                                     callback=self.uri)
            response = self._fetch(parser, url1)
            
            logging.info('RESPONSE = {}'.format(response.status_code))
            
            # check if response status is OK
            if response.status_code != 200:
                self.adapter.reset_phase(self.provider_name)
                raise Exception('Could not fetch a valid response from provider {}!'.format(self.provider_name))
            
            # extract OAuth token and save it to storage
            #oauth_token = parser(response).get('oauth_token')
            oauth_token = response.data.get('oauth_token')
            if not oauth_token:
                self.adapter.reset_phase(self.provider_name)
                raise Exception('Could not get a valid OAuth token from provider {}!'.format(self.provider_name))
            
            self.adapter.store_provider_data(self.provider_name, 'oauth_token', oauth_token)
            
            # extract OAuth token secret and save it to storage
            #oauth_token_secret = parser(response.setdefault('content'), {}).get('oauth_token_secret')
            oauth_token_secret = response.data.get('oauth_token_secret')
            if not oauth_token_secret:
                self.adapter.reset_phase(self.provider_name)
                raise Exception('Could not get a valid OAuth token secret from provider {}!'.format(self.provider_name))
            
            self.adapter.store_provider_data(self.provider_name, 'oauth_token_secret', oauth_token_secret)
                        
            # Create User Authorization URL
            url2 = simpleauth2.create_oauth1_url(url_type=2,
                                     base=self.urls[1],
                                     token=oauth_token)            
            self.adapter.redirect(url2)
        
        if self.phase == 1:
            
            # retrieve the OAuth token from session
            try:
                oauth_token = self.adapter.retrieve_provider_data(self.provider_name, 'oauth_token')
            except KeyError:
                self.adapter.reset_phase(self.provider_name)
                raise Exception('OAuth token could not be retrieved from storage!')
            
            try:
                oauth_token_secret = self.adapter.retrieve_provider_data(self.provider_name, 'oauth_token_secret')
            except KeyError:
                self.adapter.reset_phase(self.provider_name)
                raise Exception('OAuth token secret could not be retrieved from storage!')
            
            # extract the verifier
            verifier = self.adapter.get_request_param('oauth_verifier')
            if not verifier:
                self.adapter.reset_phase(self.provider_name)
                raise Exception('No OAuth verifier was returned by the {} provider!'.format(self.provider_name))
                        
            parser = self._get_parser_by_index(1)
            
            # Create Access Token URL
            url3 = simpleauth2.create_oauth1_url(url_type=3,
                                     base=self.urls[2],
                                     token=oauth_token,
                                     consumer_key=self.consumer.key,
                                     consumer_secret=self.consumer.secret,
                                     token_secret=oauth_token_secret,
                                     verifier=verifier)
            
            response = self._fetch(parser, url3, method='POST')
            
            self._update_or_create_user(response.data)
            
            self.credentials = simpleauth2.Credentials(self.consumer.access_token, self.type, self.id)
            self._update_credentials(response.data)
            
            # create event
            event = simpleauth2.AuthEvent(self, self.consumer, self.user, self.credentials)
            
            # reset phase
            self.adapter.reset_phase(self.provider_name)
            
            # call callback
            self.callback(event)

class Twitter(OAuth1):
    urls = ('https://api.twitter.com/oauth/request_token',
            'https://api.twitter.com/oauth/authorize',
            'https://api.twitter.com/oauth/access_token',
            'https://api.twitter.com/1/account/verify_credentials.json')
    
    parsers = (QUERY_STRING_PARSER, QUERY_STRING_PARSER)
    
    user_info_mapping = dict(user_id='id',
                            username='screen_name',
                            picture='profile_image_url',
                            locale='lang',
                            link='url')
    