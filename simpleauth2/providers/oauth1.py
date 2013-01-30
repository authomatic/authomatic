from simpleauth2 import providers
from simpleauth2.exceptions import DeniedError, FailureError
from urllib import urlencode
import binascii
import hashlib
import hmac
import logging
import simpleauth2
import time
import urllib
import urlparse

REQUEST_TOKEN_REQUEST_TYPE = 1
USER_AUTHORISATION_REQUEST_TYPE = 2
ACCESS_TOKEN_REQUEST_TYPE = 3
PROTECTED_RESOURCE_REQUEST_TYPE = 4

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


def _split_url(url):
    "Splits given url to url base and params converted to list of tuples"
    
    split = urlparse.urlsplit(url)
    
    base = urlparse.urlunsplit((split.scheme, split.netloc, split.path, 0, 0))
    
    params = urlparse.parse_qsl(split.query, True)
    
    return base, params


def _join_by_ampersand(*args):
    return '&'.join([simpleauth2.escape(i) for i in args])


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
        
        return _join_by_ampersand(consumer_secret, token_secret)
    
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
    
    @classmethod
    def fetch_protected_resource(cls, adapter, url, credentials, content_parser, method='GET', headers={}, response_parser=None):
        
        # check required properties of credentials
        if not (credentials.access_token and credentials.access_token_secret and credentials.consumer_key and credentials.consumer_secret):
            raise simpleauth2.exceptions.OAuth1Error('To access OAuth 1.0a resource you must provide credentials with valid access_token, ' + \
                                                     'access_token_secret, consumer_key and consumer_secret!')
        
        # create request elements
        url, payload, method = cls.create_request_elements(request_type=PROTECTED_RESOURCE_REQUEST_TYPE,
                                                           url=url,
                                                           consumer_key=credentials.consumer_key,
                                                           consumer_secret=credentials.consumer_secret,
                                                           token=credentials.access_token,
                                                           token_secret=credentials.access_token_secret,
                                                           method=method,
                                                           nonce=adapter.generate_csrf())
        
        # create rpc object
        rpc = adapter.fetch_async_2(url=url,
                                    payload=payload,
                                    method=method,
                                    headers=headers,
                                    response_parser=response_parser,
                                    content_parser=content_parser)
        # and return it
        return rpc
    
    
    @staticmethod
    def credentials_to_tuple(credentials):
        return (credentials.access_token, credentials.access_token_secret)
    
    
    @classmethod
    def credentials_from_tuple(cls, tuple_):
        short_name, access_token, access_token_secret = tuple_
        #TODO: we also need to extract consumer key and secret
        return simpleauth2.Credentials(access_token, cls.get_type(), short_name, access_token_secret=access_token_secret)
    
    
    @classmethod
    def create_request_elements(cls, request_type, url, consumer_key='', consumer_secret='',
                   token='', token_secret='', verifier='', method='GET',
                   callback='', nonce=''):
        
        # separate url base and query parameters
        url, base_params = _split_url(url)
        
        # add extracted params to future params
        params = dict(base_params)
        
        if request_type == USER_AUTHORISATION_REQUEST_TYPE:
            # no need for signature
            if token:
                params['oauth_token'] = token
            else:
                raise simpleauth2.exceptions.OAuth1Error('Parameter token is required to create User Authorization URL!')
        else:
            # signature needed
            if request_type == REQUEST_TOKEN_REQUEST_TYPE:
                # Request Token URL
                if consumer_key and consumer_secret and callback:
                    params['oauth_consumer_key'] = consumer_key
                    params['oauth_callback'] = callback
                else:
                    raise simpleauth2.exceptions.OAuth1Error('Parameters consumer_key, consumer_secret and callback are required to create Request Token URL!')
                
            elif request_type == ACCESS_TOKEN_REQUEST_TYPE:
                # Access Token URL
                if consumer_key and consumer_secret and token and verifier:
                    params['oauth_token'] = token
                    params['oauth_consumer_key'] = consumer_key
                    params['oauth_verifier'] = verifier
                else:
                    raise simpleauth2.exceptions.OAuth1Error('Parameters consumer_key, consumer_secret, token and verifier are required to create Access Token URL!')
                
            elif request_type == PROTECTED_RESOURCE_REQUEST_TYPE:
                # Protected Resources URL
                if consumer_key and consumer_secret and token and token_secret:
                    params['oauth_token'] = token
                    params['oauth_consumer_key'] = consumer_key
                else:
                    raise simpleauth2.exceptions.OAuth1Error('Parameters consumer_key, consumer_secret, token and token_secret are required to create Protected Resources URL!')
            
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
        
        payload = None
        
        if method in ('POST', 'PUT'):
            payload = params
        else:
            url = url + '?' + params
        
        return url, payload, method
    
    
    @classmethod
    def create_url(cls, url_type, base, consumer_key='', consumer_secret='',
                   token='', token_secret='', verifier='', method='GET',
                   callback='', nonce=''):
        """ Creates a HMAC-SHA1 signed url to access OAuth 1.0 endpoint"""
        
        # separate url base and query parameters
        base, base_params = _split_url(base)
        
        params = {}
        
        if url_type == REQUEST_TOKEN_REQUEST_TYPE:
            # Request Token URL
            if consumer_key and consumer_secret and callback:
                params['oauth_consumer_key'] = consumer_key
                params['oauth_callback'] = callback
            else:
                raise simpleauth2.exceptions.OAuth1Error('Parameters consumer_key, consumer_secret and callback are required to create Request Token URL!')
            
        elif url_type == USER_AUTHORISATION_REQUEST_TYPE:
            # User Authorization URL
            if token:
                params['oauth_token'] = token
                return base + '?' + urlencode(params)
            else:
                raise simpleauth2.exceptions.OAuth1Error('Parameter token is required to create User Authorization URL!')
            
        elif url_type == ACCESS_TOKEN_REQUEST_TYPE:
            # Access Token URL
            if consumer_key and consumer_secret and token and verifier:
                params['oauth_token'] = token
                params['oauth_consumer_key'] = consumer_key
                params['oauth_verifier'] = verifier
            else:
                raise simpleauth2.exceptions.OAuth1Error('Parameters consumer_key, consumer_secret, token and verifier are required to create Access Token URL!')
            
        elif url_type == PROTECTED_RESOURCE_REQUEST_TYPE:
            # Protected Resources URL
            if consumer_key and consumer_secret and token and token_secret:
                params['oauth_token'] = token
                params['oauth_consumer_key'] = consumer_key
            else:
                raise simpleauth2.exceptions.OAuth1Error('Parameters consumer_key, consumer_secret, token and token_secret are required to create Protected Resources URL!')
        
        # Sign request.
        # http://oauth.net/core/1.0a/#anchor13
        
        # Prepare parameters for signature base string
        # http://oauth.net/core/1.0a/#rfc.section.9.1
        params['oauth_signature_method'] = cls.signature_generator.method
        params['oauth_timestamp'] = str(int(time.time()))
        params['oauth_nonce'] = nonce
        params['oauth_version'] = '1.0'
        
        # add signature to params
        params['oauth_signature'] = cls.signature_generator.create_signature(method, base, params, consumer_secret, token_secret)
        
        # return signed url
        return base + '?' + urlencode(params)
    
    
    @providers._login_decorator
    def login(self, **kwargs):
        
        denied = self.adapter.get_request_param('denied')
        verifier = self.adapter.get_request_param('oauth_verifier')
        oauth_token = self.adapter.get_request_param('oauth_token')
        
        if oauth_token and verifier:
            # Phase 2 after redirect with success
            self._log(logging.INFO, 'Continuing OAuth 1.0a authorisation procedure after redirect.')
            
            oauth_token_secret = self.adapter.retrieve_provider_data(self.provider_name, 'oauth_token_secret')
            if not oauth_token_secret:
                raise FailureError('Unable to retrieve OAuth 1.0a oauth_token_secret from storage!')
                        
            # Create Access Token URL
            url3 = self.create_url(url_type=ACCESS_TOKEN_REQUEST_TYPE,
                                     base=self.urls[2],
                                     token=oauth_token,
                                     consumer_key=self.consumer.key,
                                     consumer_secret=self.consumer.secret,
                                     token_secret=oauth_token_secret,
                                     verifier=verifier,
                                     nonce=self.adapter.generate_csrf())
            
            
            self._log(logging.INFO, 'Fetching oauth token from {}.'.format(self.urls[2]))
            
            parser = self._get_parser_by_index(1)            
            response = self._fetch(parser, url3, method='POST')
            
            if response.status_code != 200:
                raise FailureError('Failed to obtain OAuth 1.0a  oauth_token from {}! HTTP status code: {}.'\
                                  .format(self.urls[2], response.status_code),
                                  code=response.status_code,
                                  url=self.urls[2])
            
            self._log(logging.INFO, 'Got oauth token.')
            
            self.credentials = simpleauth2.Credentials(self.consumer.access_token, self.get_type(), self.short_name)
            self._update_credentials(response.data)
            
            self._update_or_create_user(response.data, self.credentials)
            
            # We're done
            
        elif denied:
            # Phase 2 after redirect denied
            raise DeniedError('User denied the OAuth 1.0a request token {} during a redirect to {}!'.\
                                  format(denied, self.urls[1]),
                                  original_message=denied,
                                  url=self.urls[1])
        else:
            # Phase 1 before redirect
            self._log(logging.INFO, 'Starting OAuth 1.0a authorisation procedure.')
            
            parser = self._get_parser_by_index(0)
            
            # Create Request Token URL
            
            
            #TODO:BLOCK START seems like this block could be inside single method
            url, payload, method = self.create_request_elements(request_type=REQUEST_TOKEN_REQUEST_TYPE,
                                                                url=self.urls[0],
                                                                consumer_key=self.consumer.key,
                                                                consumer_secret=self.consumer.secret,
                                                                callback=self.uri,
                                                                nonce=self.adapter.generate_csrf())
            
            response = self.adapter.fetch_async_2(url, content_parser=parser).get_response()
            #TODO:BLOCK END
            
            
            
            # check if response status is OK
            if response.status_code != 200:
                raise FailureError('Failed to obtain oauth token from {}! HTTP status code: {}.'\
                                  .format(self.urls[0], response.status_code),
                                  code=response.status_code,
                                  url=self.urls[0])
            
            # extract OAuth token
            #oauth_token = parser(response).get('oauth_token')
            oauth_token = response.data.get('oauth_token')
            if not oauth_token:
                raise FailureError('Response from {} doesn\'t contain OAuth 1.0a oauth_token!'.format(self.urls[0]),
                                  original_message=response.data,
                                  url=self.urls[0])
            
            # extract OAuth token secret and save it to storage
            #oauth_token_secret = parser(response.setdefault('content'), {}).get('oauth_token_secret')
            oauth_token_secret = response.data.get('oauth_token_secret')
            if oauth_token_secret:
                self.adapter.store_provider_data(self.provider_name, 'oauth_token_secret', oauth_token_secret)
            else:
                raise FailureError('Failed to obtain oauth_token_secret from {}!'.format(self.urls[0]),
                                  original_message=response.data,
                                  url=self.urls[0])
            
            self._log(logging.INFO, 'Got oauth token and oauth token secret')
            
            # Create User Authorization URL
            
#            # OLD
#            url2 = self.create_url(url_type=USER_AUTHORISATION_REQUEST_TYPE,
#                                     base=self.urls[1],
#                                     token=oauth_token)
            
            # NEW
            url, payload, method = self.create_request_elements(request_type=USER_AUTHORISATION_REQUEST_TYPE,
                                                                url=self.urls[1],
                                                                token=oauth_token)
            
            self._log(logging.INFO, 'Redirecting to {}.'.format(url))
            
            self.adapter.redirect(url)


class Twitter(OAuth1):
    #TODO: dont forget to remove params!!!
    urls = ('https://api.twitter.com/oauth/request_token?pokus=kupos',
            'https://api.twitter.com/oauth/authorize?pokus=kupos',
            'https://api.twitter.com/oauth/access_token?pokus=kupos',
            'https://api.twitter.com/1/account/verify_credentials.json?pokus=kupos')
    
    parsers = (providers.QUERY_STRING_PARSER, providers.QUERY_STRING_PARSER)
    
    user_info_mapping = dict(user_id='id',
                            username='screen_name',
                            picture='profile_image_url',
                            locale='lang',
                            link='url')

