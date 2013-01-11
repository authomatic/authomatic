import exceptions
from urllib import urlencode
import binascii
import datetime
import hashlib
import hmac
import logging
import pickle
import random
import sys
import time
import urllib


def escape(s):
    """Escape a URL including any /."""
    return urllib.quote(s.encode('utf-8'), safe='~')


def create_oauth1_url(url_type, base, consumer_key=None, consumer_secret=None, token=None, token_secret=None, verifier=None, method='GET', callback=None):
    """
    Creates a HMAC-SHA1 signed url to access OAuth 1.0 endpoint
    
    Taken from the oauth2 library
        
    1. Request Token URL http://oauth.net/core/1.0a/auth_step1
        
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
    
    
    2. User Authorization URL http://oauth.net/core/1.0a/auth_step2
    
        params:
           oauth_token
        
        redirects to provider which redirects to callback
        
        returns:
           oauth_token
           oauth_verifier
    
    
    3. Access Token URL http://oauth.net/core/1.0a/auth_step3
        
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
            raise OAuth1Error('Parameters consumer_key, consumer_secret and callback are required to create Request Token URL!')
        
    elif url_type == 2:
        # User Authorization URL
        if token:
            params['oauth_token'] = token
            return base + '?' + urlencode(params)
        else:
            raise OAuth1Error('Parameter token is required to create User Authorization URL!')
        
    elif url_type == 3:
        # Access Token URL
        if consumer_key and consumer_secret and token and verifier:
            params['oauth_token'] = token
            params['oauth_consumer_key'] = consumer_key
            params['oauth_verifier'] = verifier
        else:
            raise OAuth1Error('Parameters consumer_key, consumer_secret, token and verifier are required to create Access Token URL!')
        
    elif url_type == 4:
        # Protected Resources URL
        if consumer_key and consumer_secret and token and token_secret:
            params['oauth_token'] = token
            params['oauth_consumer_key'] = consumer_key
        else:
            raise OAuth1Error('Parameters consumer_key, consumer_secret, token and token_secret are required to create Protected Resources URL!')
    
    # Tign request.
    # Taken from the oauth2 library.
    
    params['oauth_signature_method'] = 'HMAC-SHA1'
    params['oauth_timestamp'] = str(int(time.time()))
    params['oauth_nonce'] = str(random.randint(0, 100000000))
    params['oauth_version'] = '1.0'
    
    # prepare values for signing        
    # signed parameters must be sorted first by key, then by value
    params_to_sign = [(k, v) for k, v in params.items() if k != 'oauth_signature']
    params_to_sign.sort()
    params_to_sign = urllib.urlencode(params_to_sign)
    params_to_sign = params_to_sign.replace('+', '%20').replace('%7E', '~')
    
    key = '{}&'.format(escape(consumer_secret))
    if token_secret:
        key += escape(token_secret)
    
    raw = '&'.join((escape(method), escape(base), escape(params_to_sign)))
    
    # sign with HMAC-SHA1 method
    hashed = hmac.new(key, raw, hashlib.sha1)
    
    params['oauth_signature'] = binascii.b2a_base64(hashed.digest())[:-1]
    
    return base + '?' + urlencode(params)


def create_oauth2_url(url_type, base, consumer_key=None, access_token=None, redirect_uri=None, scope=None, state=None):
    
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
            raise OAuth2Error('Parameter consumer_key is required to create Authorization Requestn URL!')
    
    if url_type == 2:
        # 
        if access_token:
            params['access_token'] = access_token
        else:
            raise OAuth2Error('')
        
    return base + '?' + urlencode(params)


def resolve_provider_class(class_):
    if type(class_) in (str, unicode):
        # prepare path for simpleauth2.providers package
        path = '.'.join([__package__, 'providers', class_])
        
        # try to import class by string from providers module or by fully qualified path
        return import_string(class_, True) or import_string(path)  
    else:
        return class_


def import_string(import_name, silent=False):
    """
    Imports an object based on a string in dotted notation.
    
    taken from webapp2.import_string()
    """
    
    logging.info('import_string() import_name = {}'.format(import_name))
    try:
        if '.' in import_name:
            module, obj = import_name.rsplit('.', 1)
            return getattr(__import__(module, None, None, [obj]), obj)
        else:
            return __import__(import_name)
    except (ImportError, AttributeError), e:
        if not silent:
            raise ImportStringError(import_name, e), None, sys.exc_info()[2]


def get_provider_by_id(config, provider_id):
    for v in config.values():
        if v.get('id') == provider_id:
            return v
            break
    else:
        raise Exception('Failed to get provider by id!')


class Consumer(object):
    def __init__(self, key, secret, scope=None):
        self.key = key
        self.secret = secret
        self.scope = scope
        self.access_token = None


class User(object):
    def __init__(self, *args, **kwargs):
        self.raw_user_info = kwargs.get('raw_user_info')
        self.access_token = kwargs.get('access_token')
        self.access_token_secret = kwargs.get('access_token_secret')
        self.user_id = kwargs.get('user_id')
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


class Credentials(object):
    
    _types = ('OAuth1', 'OAuth2', 'OpenID')
    
    def __init__(self, access_token, provider_type, provider_id, consumer_key=None, consumer_secret=None, access_token_secret=None, expires_in=0):
        self.access_token = access_token
        self.provider_type = provider_type
        self.provider_id = provider_id
        self.consumer_key = consumer_key
        self.consumer_secret = consumer_secret
        self.access_token_secret = access_token_secret
        self.expires_in = expires_in
        self.expiration_date = None
    
    @property
    def expires_in(self): 
        return self._expires_in
    
    @expires_in.setter
    def expires_in(self, value):
        if value:
            self.expiration_date = datetime.datetime.now() + datetime.timedelta(seconds=int(value))
            self._expires_in = value
    
    def serialize(self):
        # OAuth 2.0 needs only access_token
        result = (self._types.index(self.provider_type), self.provider_id, self.access_token)
        
        if self.provider_type == 'OAuth1':
            # OAuth 1.0 also needs access_token_secret
            result += (self.access_token_secret,)
        elif self.provider_type == 'OAuth2':
            # OAuth 2.0 also needs expires_in
            result += (self.expiration_date,)
        return pickle.dumps(result)
    
    @classmethod
    def from_serialized(cls, adapter, serialized):
        # Unpickle serialized
        deserialized = pickle.loads(serialized)
        
        try:
            provider_type = cls._types[deserialized[0]]
            provider_id = deserialized[1]
            access_token = deserialized[2]
            
            cfg =  get_provider_by_id(adapter.get_providers_config(), provider_id)
            
            if provider_type == 'OAuth2':
                credentials = cls(access_token, provider_type, provider_id)
                credentials.expiration_date = deserialized[3]
                return credentials
            
            elif provider_type == 'OAuth1':
                return cls(access_token, provider_type, provider_id,
                           access_token_secret=deserialized[3],
                           consumer_key=cfg.get('consumer_key'),
                           consumer_secret=cfg.get('consumer_secret'))
            
        except (TypeError, IndexError) as e:
            raise CredentialsError('Deserialization failed! Error: {}'.format(e))


class AuthEvent(object):
    def __init__(self, provider, consumer, user, credentials):
        self.provider = provider
        self.consumer = consumer
        self.user = user
        self.credentials = credentials


class RPC(object):
    """
    Remote Procedure Call wrapper
    """
    
    def __init__(self, rpc_object, response_parser, content_parser):
        self.rpc_object = rpc_object
        self.response_parser = response_parser
        self.content_parser = content_parser
    
    def get_response(self):
        """
        Returns Response instance
        """
        
        return self.response_parser(self.rpc_object.get_result(), self.content_parser)


class Response(object):
    """
    Provides unified interface to results of different http request types
    """
    
    def __init__(self, status_code=None, headers=None, raw_content=None, content=None):
        self.raw_content = raw_content
        self.status_code = status_code
        self.headers = headers
        self.content = content


class UserInfoResponse(object):
    def __init__(self, response, user):
        self.raw_content = response.raw_content
        self.status_code = response.status_code
        self.headers = response.headers
        self.content = response.content
        self.user = user


class Request(object):
    def __init__(self, adapter, url, credentials, method='GET', response_parser=None, content_parser=None):
        self.adapter = adapter
        self.url = url
        self.credentials = credentials
        self.method = method
        self.response_parser = response_parser
        self.content_parser = content_parser or adapter.json_parser
        
        self.rpc = None
        
        if self.credentials.provider_type == 'OAuth2':
            self.url = create_oauth2_url(2, url, access_token=self.credentials.access_token)
        elif self.credentials.provider_type == 'OAuth1':
            self.url = create_oauth1_url(url_type=4,
                                         base=url,
                                         consumer_key=self.credentials.consumer_key,
                                         consumer_secret=self.credentials.consumer_secret,
                                         token=self.credentials.access_token,
                                         token_secret=self.credentials.access_token_secret)
    
    def fetch(self):
        self.rpc = self.adapter.fetch_async(self.content_parser, self.url,
                                            method=self.method,
                                            response_parser=self.response_parser)        
        return self
    
    def get_response(self):
        return self.rpc.get_response()
