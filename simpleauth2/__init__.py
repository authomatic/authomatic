import exceptions
import providers
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

def login(adapter, provider_name, callback, scope=[]):
    
    providers_config = adapter.get_providers_config()
            
    # retrieve required settings for current provider and raise exceptions if missing
    provider_settings = providers_config.get(provider_name)
    if not provider_settings:
        raise exceptions.ConfigError('Provider name "{}" not specified!'.format(provider_name))
    
    provider_class = provider_settings.get('class_name')
    if not provider_class:
        raise exceptions.ConfigError('Class name not specified for provider {}!'.format(provider_name))
    
    consumer_key = provider_settings.get('consumer_key')
    if not consumer_key:
        raise exceptions.ConfigError('Consumer key not specified for provider {}!'.format(provider_name))    
    
    consumer_secret = provider_settings.get('consumer_secret')
    if not consumer_secret:
        raise exceptions.ConfigError('Consumer secret not specified for provider {}!'.format(provider_name))
    
    # merge scopes from config and argument
    scope = provider_settings.get('scope', []) + scope
    
    # create consumer
    consumer = Consumer(consumer_key, consumer_secret, scope)
    
    # get phase
    phase = adapter.get_phase(provider_name)
    
    # store increased phase
    adapter.set_phase(provider_name, phase + 1)
    
        
    ProviderClass = resolve_provider_class(provider_class)
    
    # instantiate and call provider class
    ProviderClass(adapter, phase, provider_name, consumer, callback, provider_settings.get('short_name')).login()


def escape(s):
    """Escape a URL including any /."""
    return urllib.quote(s.encode('utf-8'), safe='~')


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
            raise exceptions.ImportStringError(import_name, e), None, sys.exc_info()[2]


def get_provider_by_id(config, provider_id):
    for v in config.values():
        if v.get('short_name') == provider_id:
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
    
    def __init__(self, access_token, provider_type, short_name, consumer_key=None, consumer_secret=None, access_token_secret=None, expires_in=0):
        self.access_token = access_token
        self.provider_type = provider_type
        self.provider_short_name = short_name
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
        result = (self.provider_short_name, self.access_token)
        
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
            provider_id = deserialized[0]
            access_token = deserialized[1]
            
            cfg =  get_provider_by_id(adapter.get_providers_config(), provider_id)
            
            ProviderClass = resolve_provider_class(cfg.get('class_name'))
            provider_type = ProviderClass.get_type()
            
            if provider_type == 'OAuth2':
                credentials = cls(access_token, provider_type, provider_id)
                credentials.expiration_date = deserialized[2]
                return credentials
            
            elif provider_type == 'OAuth1':
                return cls(access_token, provider_type, provider_id,
                           access_token_secret=deserialized[2],
                           consumer_key=cfg.get('consumer_key'),
                           consumer_secret=cfg.get('consumer_secret'))
            
        except (TypeError, IndexError) as e:
            raise exceptions.CredentialsError('Deserialization failed! Error: {}'.format(e))


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
    
    def __init__(self, content_parser, status_code=None, headers=None, content=None):
        self.content_parser = content_parser
        self.status_code = status_code
        self.headers = headers
        self.content = content
        self._data = None
    
    @property
    def data(self):
        if not self._data:
            self._data = self.content_parser(self.content)
        return self._data


class UserInfoResponse(object):
    def __init__(self, response, user):
        self.status_code = response.status_code
        self.headers = response.headers
        self.content = response.content
        self.data = response.data
        self.user = user


class Request(object):
    def __init__(self, adapter, url, credentials, method='GET', response_parser=None, content_parser=None):
        self.adapter = adapter
        self.url = url
        self.method = method
        self.response_parser = response_parser
        self.content_parser = content_parser or adapter.json_parser
        self.rpc = None
        
        if type(credentials) == Credentials:
            self.credentials = credentials
        elif type(credentials) == str:
            self.credentials = Credentials.from_serialized(self.adapter, credentials)
        
        if self.credentials.provider_type == 'OAuth2':
            self.url = providers.OAuth2.create_url(2, url, access_token=self.credentials.access_token)
        elif self.credentials.provider_type == 'OAuth1':
            self.url = providers.OAuth1.create_url(url_type=4,
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
