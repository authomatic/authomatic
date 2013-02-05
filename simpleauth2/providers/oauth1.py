from simpleauth2 import providers
from simpleauth2.exceptions import CancellationError, FailureError, OAuth1Error
from urllib import urlencode
import abc
import binascii
import hashlib
import hmac
import logging
import simpleauth2.core as core
import time
import urllib
import urlparse


def _normalize_params(params):
    """
    Returns a normalized query string sorted first by key, then by value
    excluding the "realm" and "oauth_signature" parameters
    as specified here: http://oauth.net/core/1.0a/#rfc.section.9.1.1
    
    params: dict or list of tuples
    """
    
    if type(params) == dict:
        params = params.items()
    
    # remove "realm" and "oauth_signature"
    params = [(k, v) for k, v in params if k not in ('oauth_signature', 'realm')]
    # sort
    params.sort()
    # convert to query string
    qs = urllib.urlencode(params)
    # replace "+" to "%20"
    qs = qs.replace('+', '%20')
    # replace "%7E" to "%20"
    qs = qs.replace('%7E', '~')
    
    return qs



def _join_by_ampersand(*args):
    return '&'.join([core.escape(i) for i in args])


def _create_base_string(method, base, params):
    """
    Returns base string for HMAC-SHA1 signature
    
    as specified at: http://oauth.net/core/1.0a/#rfc.section.9.1.3
    """
    
    normalized_qs = _normalize_params(params)
    
    return _join_by_ampersand(method, base, normalized_qs)


class BaseSignatureGenerator(object):
    
    method = ''
    
    @classmethod
    def create_signature(cls, method, base, params, consumer_secret, token_secret=''):
        raise NotImplementedError


class HMACSHA1Generator(BaseSignatureGenerator):
    
    method = 'HMAC-SHA1'
    
    @classmethod
    def _create_key(cls, consumer_secret, token_secret=''):
        """
        Returns a key for HMAC-SHA1 signature
        
        as specified at: http://oauth.net/core/1.0a/#rfc.section.9.2
        
        :param consumer_secret:
        :param token_secret:
        """
        
        return _join_by_ampersand(consumer_secret, token_secret or '')
    
    @classmethod
    def create_signature(cls, method, base, params, consumer_secret, token_secret=''):
        """
        Returns HMAC-SHA1 signature
        
        as specified at: http://oauth.net/core/1.0a/#rfc.section.9.2
        
        :param cls:
        :param method:
        :param base:
        :param params:
        :param consumer_secret:
        :param token_secret:
        """
        
        base_string = _create_base_string(method, base, params)
        key = cls._create_key(consumer_secret, token_secret)
        
        hashed = hmac.new(key, base_string, hashlib.sha1)
        signature = binascii.b2a_base64(hashed.digest())[:-1]
        
        return signature


class OAuth1(providers.AuthorisationProvider):
    
    signature_generator = HMACSHA1Generator
    
    REQUEST_TOKEN_REQUEST_TYPE = 1
    
    def __init__(self, *args, **kwargs):
        super(OAuth1, self).__init__(*args, **kwargs)
        
        # create keys under which oauth token and secret will be stored in session
        self._oauth_token_key = self.provider_name + '_oauth_token'
        self._oauth_token_secret_key = self.provider_name + '_oauth_token_secret'
        
        
    #===========================================================================
    # Abstract properties
    #===========================================================================
    
    @abc.abstractproperty
    def request_token_url(self):
        pass
    
    
    #===========================================================================
    # Internal methods
    #===========================================================================
    
    @classmethod
    def _create_request_elements(cls, request_type, credentials, url, method='GET',
                                 verifier='', callback='', nonce=''):
        
        consumer_key = credentials.consumer_key or ''
        consumer_secret = credentials.consumer_secret or ''
        token = credentials.token or ''
        token_secret = credentials.token_secret or ''
        
        # separate url base and query parameters
        url, base_params = cls._split_url(url)
        
        # add extracted params to future params
        params = dict(base_params)
        
        if request_type == cls.USER_AUTHORISATION_REQUEST_TYPE:
            # no need for signature
            if token:
                params['oauth_token'] = token
            else:
                raise OAuth1Error('Credentials with valid token are required to create User Authorization URL!')
        else:
            # signature needed
            if request_type == cls.REQUEST_TOKEN_REQUEST_TYPE:
                # Request Token URL
                if consumer_key and consumer_secret and callback:
                    params['oauth_consumer_key'] = consumer_key
                    params['oauth_callback'] = callback
                else:
                    raise OAuth1Error('Credentials with valid consumer_key, consumer_secret and ' +\
                                                             'callback are required to create Request Token URL!')
                
            elif request_type == cls.ACCESS_TOKEN_REQUEST_TYPE:
                # Access Token URL
                if consumer_key and consumer_secret and token and verifier:
                    params['oauth_token'] = token
                    params['oauth_consumer_key'] = consumer_key
                    params['oauth_verifier'] = verifier
                else:
                    raise OAuth1Error('Credentials with valid consumer_key, consumer_secret, token ' +\
                                                             'and argument verifier are required to create Access Token URL!')
                
            elif request_type == cls.PROTECTED_RESOURCE_REQUEST_TYPE:
                # Protected Resources URL
                if consumer_key and consumer_secret and token and token_secret:
                    params['oauth_token'] = token
                    params['oauth_consumer_key'] = consumer_key
                else:
                    raise OAuth1Error('Credentials with valid consumer_key, consumer_secret, token and ' +\
                                                             'token_secret are required to create Protected Resources URL!')
            
            # Sign request.
            # http://oauth.net/core/1.0a/#anchor13
            
            # Prepare parameters for signature base string
            # http://oauth.net/core/1.0a/#rfc.section.9.1
            params['oauth_signature_method'] = cls.signature_generator.method
            params['oauth_timestamp'] = str(int(time.time()))
            params['oauth_nonce'] = nonce
            params['oauth_version'] = '1.0'
            
            # add signature to params
            params['oauth_signature'] = cls.signature_generator.create_signature(method, url, params, consumer_secret, token_secret)
        
        
        params = urlencode(params)
        
        body = None
        
        if method in ('POST', 'PUT'):
            body = params
        else:
            url = url + '?' + params
        
        return url, body, method
    
    
    #===========================================================================
    # Exposed methods
    #===========================================================================
    
    @classmethod
    def fetch_protected_resource(cls, adapter, url, credentials, content_parser, method='GET', headers={}, response_parser=None):
        
        # check required properties of credentials
        if not (credentials.token and credentials.token_secret and credentials.consumer_key and credentials.consumer_secret):
            raise OAuth1Error('To access OAuth 1.0a resource you must provide credentials with valid access_token, ' + \
                                                     'access_token_secret, consumer_key and consumer_secret!')
        
        # create request elements
        request_elements = cls._create_request_elements(request_type=cls.PROTECTED_RESOURCE_REQUEST_TYPE,
                                                       credentials=credentials,
                                                       url=url,
                                                       method=method,
                                                       nonce=cls._generate_csrf())
        
        # create rpc object
        rpc = adapter.fetch_async(*request_elements,
                                    headers=headers,
                                    response_parser=response_parser,
                                    content_parser=content_parser)
        # and return it
        return rpc
    
    
    @staticmethod
    def to_tuple(credentials):
        return (credentials.token, credentials.token_secret)
    
    
    @classmethod
    def reconstruct(cls, deserialized_tuple, cfg):
        provider_short_name, token, token_secret = deserialized_tuple
        
        return core.Credentials(token=token,
                                       token_secret=token_secret,
                                       provider_type=cls.get_type(),
                                       provider_short_name=provider_short_name,
                                       consumer_key=cfg.get('consumer_key'),
                                       consumer_secret=cfg.get('consumer_secret'))
    
    
    @providers._login_decorator
    def login(self, **kwargs):
        
        credentials = core.Credentials(provider=self)
        
        # get request parameters from which we can determine the login phase
        denied = self.adapter.params.get('denied')
        verifier = self.adapter.params.get('oauth_verifier')
        request_token = self.adapter.params.get('oauth_token')
        
        if request_token and verifier:
            # Phase 2 after redirect with success
            self._log(logging.INFO, 'Continuing OAuth 1.0a authorisation procedure after redirect.')
            token_secret = self._session_get('token_secret')
            if not token_secret:
                raise FailureError('Unable to retrieve token secret from storage!')
            
            # Get Access Token          
            self._log(logging.INFO, 'Fetching for access token from {}.'.format(self.access_token_url))
            
            credentials.token = request_token
            credentials.token_secret = token_secret
            
            request_elements = self._create_request_elements(request_type=self.ACCESS_TOKEN_REQUEST_TYPE,
                                                             url=self.access_token_url,
                                                             credentials=credentials,
                                                             verifier=verifier,
                                                             nonce=self._generate_csrf())
            
            response = self._fetch(*request_elements)
            
            if response.status_code != 200:
                raise FailureError('Failed to obtain OAuth 1.0a  oauth_token from {}! HTTP status code: {}.'\
                                   .format(self.access_token_url, response.status_code),
                                   code=response.status_code,
                                   url=self.access_token_url)
            
            self._log(logging.INFO, 'Got access token.')
            
            credentials.token = response.data.get('oauth_token')
            credentials.token_secret = response.data.get('oauth_token_secret')
            
            credentials = self._credentials_parser(credentials, response.data)
            
            self._update_or_create_user(response.data, credentials)
            
            #===================================================================
            # We're done!
            #===================================================================
            
        elif denied:
            # Phase 2 after redirect denied
            raise CancellationError('User denied the request token {} during a redirect to {}!'.\
                                  format(denied, self.user_authorisation_url),
                                  original_message=denied,
                                  url=self.user_authorisation_url)
        else:
            # Phase 1 before redirect
            self._log(logging.INFO, 'Starting OAuth 1.0a authorisation procedure.')
            
            # Fetch for request token
            request_elements = self._create_request_elements(request_type=self.REQUEST_TOKEN_REQUEST_TYPE,
                                                             credentials=credentials,
                                                             url=self.request_token_url,
                                                             callback=self.uri,
                                                             nonce=self._generate_csrf())
            
            self._log(logging.INFO, 'Fetching for request token and token secret.')
            response = self._fetch(*request_elements)
            
            # check if response status is OK
            if response.status_code != 200:
                raise FailureError('Failed to obtain request token from {}! HTTP status code: {}.'\
                                  .format(self.request_token_url, response.status_code),
                                  code=response.status_code,
                                  url=self.request_token_url)
            
            # extract request token
            request_token = response.data.get('oauth_token')
            if not request_token:
                raise FailureError('Response from {} doesn\'t contain oauth_token parameter!'.format(self.request_token_url),
                                  original_message=response.data,
                                  url=self.request_token_url)
            
            # we need request token for user authorisation redirect
            credentials.token = request_token
                        
            # extract token secret and save it to storage
            token_secret = response.data.get('oauth_token_secret')
            if token_secret:
                # we need token secret after user authorisation redirect to get access token
                self._session_set('token_secret', token_secret)
            else:
                raise FailureError('Failed to obtain token secret from {}!'.format(self.request_token_url),
                                  original_message=response.data,
                                  url=self.request_token_url)
            
            
            self._log(logging.INFO, 'Got request token and token secret')
            
            # Create User Authorization URL
            request_elements = self._create_request_elements(request_type=self.USER_AUTHORISATION_REQUEST_TYPE,
                                                             credentials=credentials,
                                                             url=self.user_authorisation_url)
            
            self._log(logging.INFO, 'Redirecting user to {}.'.format(request_elements[0]))
            
            self.adapter.redirect(request_elements[0])


class Twitter(OAuth1):
    
    request_token_url = 'https://api.twitter.com/oauth/request_token'
    user_authorisation_url = 'https://api.twitter.com/oauth/authorize'
    access_token_url = 'https://api.twitter.com/oauth/access_token'
    user_info_url = 'https://api.twitter.com/1/account/verify_credentials.json'
    
    @staticmethod
    def _user_parser(user, data):
        user.user_id = data.get('id')
        user.username = data.get('screen_name')
        user.picture = data.get('profile_image_url')
        user.locale = data.get('lang')
        user.link = data.get('url')
        return user

