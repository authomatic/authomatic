from urllib import urlencode
import binascii
import hashlib
import hmac
import logging
import oauth2
import random
import simpleauth2
import time
import urllib

QUERY_STRING_PARSER = 'query_string_parser'
JSON_PARSER = 'json_parser'

HTTP_METHODS = ('GET', 'HEAD', 'POST', 'PUT', 'DELETE', 'TRACE', 'OPTIONS', 'CONNECT', 'PATCH')

class BaseProvider(object):
    """
    Base class for all providers
    """
    
    def __init__(self, adapter, provider_name, consumer, callback, short_name=None):
        self.provider_name = provider_name
        self.consumer = consumer
        self.callback = callback
        self.adapter = adapter
        self.short_name = short_name
        
        self.user = None
        self._phase = None
                
        self._user_info_request = None
        
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
    
    @classmethod
    def get_type(cls):
        return cls.__bases__[0].__name__
        
    @staticmethod
    def create_url(url_type, base):
        raise NotImplementedError
    
    
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
    
    @property
    def phase(self):
        if self._phase is None:
            self._phase = self.adapter.get_phase(self.provider_name)
        return self._phase
    
    #===========================================================================
    # Internal methods
    #===========================================================================
    
    def _increase_phase(self):
        self.adapter.set_phase(self.provider_name, self.phase + 1)
        
    
    def _fetch(self, content_parser, url, params={}, method='GET', headers={}):
        #TODO: Check whether the method is valid
        if not method in HTTP_METHODS:
            raise simpleauth2.exceptions.HTTPError('The {} is not a valid HTTP method!'.format(method))
        
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
    
    
    def _check_consumer(self):
        if not self.consumer.key:
            raise simpleauth2.exceptions.ConfigError('Consumer key not specified for provider {}!'.format(self.provider_name))
        
        if not self.consumer.secret:
            raise simpleauth2.exceptions.ConfigError('Consumer key not specified for provider {}!'.format(self.provider_name))
    

#===============================================================================
# OAuth 2.0
#===============================================================================

class OAuth2(BaseProvider):
    """
    Base class for OAuth2 services
    """
        
    @staticmethod
    def create_url(url_type, base, consumer_key=None, access_token=None, redirect_uri=None, scope=None, state=None):
        
        params = {}
        
        if url_type == 1:
            # Authorization Request http://tools.ietf.org/html/draft-ietf-oauth-v2-31#section-4.1.1
            if consumer_key:
                # required
                params['client_id'] = consumer_key
                params['response_type'] = 'code'
                
                # optional
                if redirect_uri: params['redirect_uri'] = redirect_uri
                if scope: params['scope'] = scope
                if state: params['state'] = state
            else:
                raise simpleauth2.exceptions.OAuth2Error('Parameter consumer_key is required to create Authorization Requestn URL!')
        
        if url_type == 2:
            # 
            if access_token:
                params['access_token'] = access_token
            else:
                raise simpleauth2.exceptions.OAuth2Error('')
            
        return base + '?' + urlencode(params)
     
    def login(self):
        
        self._check_consumer()
        
        if self.phase == 0:
            
            self._increase_phase()
            
            # generate csfr
            csrf_token = self.adapter.generate_csrf()
            self.adapter.store_provider_data(self.provider_name, 'csrf_token', csrf_token)
            
            url = self.create_url(1, self.urls[0],
                                    consumer_key=self.consumer.key,
                                    redirect_uri=self.uri,
                                    scope=self._normalize_scope(self.consumer.scope),
                                    state=csrf_token)
            
            self.adapter.redirect(url)
            
        if self.phase == 1:
            
            # Validate CSRF token
            csrf_token = self.adapter.retrieve_provider_data(self.provider_name, 'csrf_token')
            state = self.adapter.get_request_param('state')
            if not csrf_token == state:
                raise simpleauth2.exceptions.CSRFError("The value {} of the \"state\" parameter returned by the provider doesn't match with the saved CSRF token!".format(state))
            
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
            self.credentials = simpleauth2.Credentials(response.data.get('access_token'), self.get_type(), self.short_name)
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
    
    user_info_mapping = dict(user_id='short_name',
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
                            user_id='short_name')
    
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
    
    user_info_mapping=dict(user_id='short_name',
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
        credentials.provider_type = self.get_type()
        
        return credentials    
    
    
    @staticmethod
    def create_url(url_type, base, consumer_key=None, consumer_secret=None, token=None, token_secret=None, verifier=None, method='GET', callback=None, nonce=None):
        """
        Creates a HMAC-SHA1 signed url to access OAuth 1.0 endpoint
        
        Taken from the oauth2 library
            
        1. Request Token URL http://oauth.net/core/1.0a/#auth_step1
            
            params:
               oauth_consumer_key
               
               oauth_callback (must be "oob" if not used with redirect)
               
               oauth_signature_method
               oauth_timestamp
               oauth_nonce
               oauth_version
               
               oauth_signature (we need consumer_secret to sign the request)
            
            returns:
               oauth_token
               oauth_token_secret
               oauth_callback_confirmed
        
        
        2. User Authorization URL http://oauth.net/core/1.0a/#auth_step2
        
            params:
               oauth_token
            
            redirects to provider which redirects to callback
            
            returns:
               oauth_token
               oauth_verifier
        
        
        3. Access Token URL http://oauth.net/core/1.0a/#auth_step3
            
            params:
                oauth_consumer_key
                oauth_token            
                oauth_verifier
                
                oauth_signature_method
                oauth_timestamp
                oauth_nonce
                oauth_version
                
                oauth_signature (we need consumer_secret to sign the request)
                
            returns:
                oauth_token
                oauth_token_secret
        
        
        4. Protected Resources URL http://oauth.net/core/1.0a/#anchor12
            
            params:
                oauth_consumer_key
                oauth_token
                
                oauth_signature_method
                oauth_timestamp
                oauth_nonce
                oauth_version
                
                oauth_signature (we need consumer_secret and token_secret to sign the request)
                
            returns:
                requested data    
        
        """
        
        params = {}
        
        if url_type == 1:
            # Request Token URL
            if consumer_key and consumer_secret and callback:
                params['oauth_consumer_key'] = consumer_key
                params['oauth_callback'] = callback
            else:
                raise simpleauth2.exceptions.OAuth1Error('Parameters consumer_key, consumer_secret and callback are required to create Request Token URL!')
            
        elif url_type == 2:
            # User Authorization URL
            if token:
                params['oauth_token'] = token
                return base + '?' + urlencode(params)
            else:
                raise simpleauth2.exceptions.OAuth1Error('Parameter token is required to create User Authorization URL!')
            
        elif url_type == 3:
            # Access Token URL
            if consumer_key and consumer_secret and token and verifier:
                params['oauth_token'] = token
                params['oauth_consumer_key'] = consumer_key
                params['oauth_verifier'] = verifier
            else:
                raise simpleauth2.exceptions.OAuth1Error('Parameters consumer_key, consumer_secret, token and verifier are required to create Access Token URL!')
            
        elif url_type == 4:
            # Protected Resources URL
            if consumer_key and consumer_secret and token and token_secret:
                params['oauth_token'] = token
                params['oauth_consumer_key'] = consumer_key
            else:
                raise simpleauth2.exceptions.OAuth1Error('Parameters consumer_key, consumer_secret, token and token_secret are required to create Protected Resources URL!')
        
        # Tign request.
        # Taken from the oauth2 library.
        
        params['oauth_signature_method'] = 'HMAC-SHA1'
        params['oauth_timestamp'] = str(int(time.time()))
        params['oauth_nonce'] = nonce
        params['oauth_version'] = '1.0'
        
        # prepare values for signing        
        # signed parameters must be sorted first by key, then by value
        params_to_sign = [(k, v) for k, v in params.items() if k != 'oauth_signature']
        params_to_sign.sort()
        params_to_sign = urllib.urlencode(params_to_sign)
        params_to_sign = params_to_sign.replace('+', '%20').replace('%7E', '~')
        
        key = '{}&'.format(simpleauth2.escape(consumer_secret))
        if token_secret:
            key += simpleauth2.escape(token_secret)
        
        raw = '&'.join((simpleauth2.escape(method),
                        simpleauth2.escape(base),
                        simpleauth2.escape(params_to_sign)))
        
        # sign with HMAC-SHA1 method
        hashed = hmac.new(key, raw, hashlib.sha1)
        
        params['oauth_signature'] = binascii.b2a_base64(hashed.digest())[:-1]
        
        return base + '?' + urlencode(params)
    
    def login(self):
        
        self._check_consumer()
        
        if self.phase == 0:
            
            self._increase_phase()
            
            parser = self._get_parser_by_index(0)
            
            # Create Request Token URL
            url1 = self.create_url(url_type=1,
                                     base=self.urls[0],
                                     consumer_key=self.consumer.key,
                                     consumer_secret=self.consumer.secret,
                                     callback=self.uri,
                                     nonce=self.adapter.generate_csrf())
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
            url2 = self.create_url(url_type=2,
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
            url3 = self.create_url(url_type=3,
                                     base=self.urls[2],
                                     token=oauth_token,
                                     consumer_key=self.consumer.key,
                                     consumer_secret=self.consumer.secret,
                                     token_secret=oauth_token_secret,
                                     verifier=verifier,
                                     nonce=self.adapter.generate_csrf())
            
            response = self._fetch(parser, url3, method='POST')
            
            self._update_or_create_user(response.data)
            
            self.credentials = simpleauth2.Credentials(self.consumer.access_token, self.get_type(), self.short_name)
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
    
    user_info_mapping = dict(user_id='short_name',
                            username='screen_name',
                            picture='profile_image_url',
                            locale='lang',
                            link='url')


#TODO: Implement OpenID providers


#===============================================================================
# Open ID
#===============================================================================

class OpenID(BaseProvider):
    
    @staticmethod
    def _create_url(identity, callback):
        return 'abc'
    
    @staticmethod
    def _normalize_identifier(identifier):
        return identifier
    
    def login(self):
        logging.info('Open ID provider = {}'.format(self.provider_name))
        
        url = self._create_url(self.urls[0], self.uri)
        
        logging.info('Open ID url1 = {}'.format(url))
        
        if self.phase == 0:
            
            # get identifier
            identifier = self.urls[0] or self.adapter.get_request_param('identifier')
            
            # 1.) Normalize Open ID identifier http://openid.net/specs/openid-authentication-2_0.html#normalization
            identifier = self._normalize_identifier(identifier)
            
            # 2.) Discover http://openid.net/specs/openid-authentication-2_0.html#normalization
            #
            # should return
            #    provider endpoint URL
            #    protocol version
            # or
            #    claimed identifier
            #    provider local identifier
            # or
            #    XRDS document (xml)
            
            
            # 3.) Establish association http://openid.net/specs/openid-authentication-2_0.html#associations
            #
            #    fetch provider with parameters:
            #        common parameters:
            #            openid.ns
            #            openid.mode
            #            openid.assoc_type
            #                HMAC-SHA1
            #                HMAC-SHA256
            #            openid.session_type
            #                no-encryption
            #                DH-SHA1
            #                DH-SHA256
            #
            #        Diffie-Hellman Request Parameters:
            #            openid.dh_modulus
            #            openid.dh_gen
            #            openid.dh_consumer_public
            #
            #    on success returns
            #        common parameters:
            #            ns
            #            assoc_handle
            #            session_type
            #            assoc_type
            #            expires_in
            #
            #        Unencrypted Response Parameters:
            #            mac_key
            #
            #        Diffie-Hellman Response Parameters:
            #            dh_server_public
            #            enc_mac_key
            #
            #    on failure returns:
            #        ns
            #        error
            #        error_code
            #        session_type
            #        assoc_type
            
            
            # 4.) Request Authentication http://openid.net/specs/openid-authentication-2_0.html#requesting_authentication
            #
            #    redirect to provider with parameters:
            #        openid.ns
            #        openid.mode
            #            checkid_immediate
            #            checkid_setup
            #        openid.claimed_id
            #        openid.identity
            #        openid.assoc_handle
            #        openid.return_to
            #        openid.realm
            #
            #    on success returns:
            #        openid.ns
            #        openid.mode
            #        openid.op_endpoint
            #        openid.claimed_id
            #        openid.identity
            #        openid.return_to
            #        openid.response_nonce
            #        openid.invalidate_handle
            #        openid.assoc_handle
            #        openid.signed
            #        openid.sig
            #
            #    on failure returns:
            #        openid.ns
            #        openid.mode
                        
            
            pass
        
        elif self.phase == 1:
            
            # 5.) Verify assertion http://openid.net/specs/openid-authentication-2_0.html#verification
            #
            
            # Finally we get
            #
            #    openid.claimed_id (visible user id)
            #    
            
            pass

class Yahoo(OpenID):
    urls = ('me.yahoo.com', )

































































    