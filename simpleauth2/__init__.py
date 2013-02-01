import exceptions
import providers
from urllib import urlencode
import binascii
import datetime
import hashlib
import hmac
import pickle
import random
import sys
import time
import urllib


def login(adapter, provider_name, callback=None, report_errors=True, logging_level=20, scope=[], **kwargs):
    
    providers_config = adapter.get_providers_config()
            
    # retrieve required settings for current provider and raise exceptions if missing
    provider_settings = providers_config.get(provider_name)
    if not provider_settings:
        raise exceptions.ConfigError('Provider name "{}" not specified!'.format(provider_name))
    
    provider_class = provider_settings.get('class_name')
    if not provider_class:
        raise exceptions.ConfigError('Class name not specified for provider {}!'.format(provider_name))
        
    # merge scopes from config and argument
    scope = provider_settings.get('scope', []) + scope
    
    # create consumer
    consumer = Consumer(provider_settings.get('consumer_key'),
                        provider_settings.get('consumer_secret'),
                        scope)
        
    ProviderClass = resolve_provider_class(provider_class)
    
    # instantiate provider class
    provider = ProviderClass(adapter, provider_name, consumer, callback, provider_settings.get('short_name'),
                             report_errors=report_errors,
                             logging_level=logging_level)
    
    # return login result
    return provider.login(**kwargs)


class Counter(object):
    count = 0
    def __call__(self):
        self.count += 1
        return self.count


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
    
    try:
        if '.' in import_name:
            module, obj = import_name.rsplit('.', 1)
            return getattr(__import__(module, None, None, [obj]), obj)
        else:
            return __import__(import_name)
    except (ImportError, AttributeError), e:
        if not silent:
            raise exceptions.ImportStringError(import_name, e), None, sys.exc_info()[2]


def get_provider_settings_by_short_name(config, provider_id):
    for v in config.values():
        if v.get('short_name') == provider_id:
            return v
            break
    else:
        raise Exception('Failed to get provider by id "{}"!'.format(provider_id))


class Consumer(object):
    def __init__(self, key, secret, scope=None):
        self.key = key
        self.secret = secret
        self.scope = scope


class User(object):
    def __init__(self, provider, **kwargs):
        self.provider = provider
        self.credentials = kwargs.get('credentials')
        
        self.raw_user_info = kwargs.get('raw_user_info')
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
        self.birth_date = kwargs.get('birth_date')
        self.nickname = kwargs.get('nickname')
        self.country = kwargs.get('country')
        self.postal_code = kwargs.get('postal_code')
        self.gae_user = kwargs.get('gae_user')
    
    def update(self):
        return self.provider.update_user()


class Credentials(object):
    
    def __init__(self, **kwargs):
        
        self.token = kwargs.get('token')
        self.token_secret = kwargs.get('token_secret')
        
        self.expires_in = kwargs.get('expires_in', 0)
        self.expiration_date = kwargs.get('expiration_date')
        
        provider = kwargs.get('provider')
        consumer = kwargs.get('consumer')
        
        if provider:
            self.provider_type = provider.get_type()
            self.provider_short_name = provider.short_name
            self.consumer_key = provider.consumer.key
            self.consumer_secret = provider.consumer.secret
        elif consumer:
            self.consumer_key = consumer.key
            self.consumer_secret = consumer.secret
        else:
            self.provider_type = kwargs.get('provider_type')
            self.provider_short_name = kwargs.get('provider_short_name')
            
            self.consumer_key = kwargs.get('consumer_key')
            self.consumer_secret = kwargs.get('consumer_secret')
            
    
    @property
    def expires_in(self): 
        return self._expires_in
    
    @expires_in.setter
    def expires_in(self, value):
        if value:
            self.expiration_date = datetime.datetime.now() + datetime.timedelta(seconds=int(value))
            self._expires_in = value
    
    def get_provider_class(self):
        return resolve_provider_class(self.provider_type)
    
    def serialize(self):
        
        # short_name will be the first item by all providers
        short_name = self.provider_short_name
        if short_name is None:
            raise exceptions.ConfigError('The provider config must have a "short_name" key set to a unique value to be able to serialize credentials!')
        rest = self.get_provider_class().to_tuple(self)
        
        result = (short_name, ) + rest
        
        return pickle.dumps(result)
    
    
    @classmethod
    def deserialize(cls, adapter, serialized):
        
        # Unpickle serialized
        deserialized = pickle.loads(serialized)
        
        try:
            provider_id = deserialized[0]
            
            cfg =  get_provider_settings_by_short_name(adapter.get_providers_config(), provider_id)
            
            ProviderClass = resolve_provider_class(cfg.get('class_name'))
            
            return ProviderClass.reconstruct(deserialized, cfg)
                        
        except (TypeError, IndexError) as e:
            raise exceptions.CredentialsError('Deserialization failed! Error: {}'.format(e))


class LoginResult(object):
    def __init__(self, provider, error=None):
        self.provider = provider
        self.error = error
        self.consumer = provider.consumer
        self.user = provider.user


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
            self.credentials = Credentials.deserialize(self.adapter, credentials)
    
    def fetch(self):        
        ProviderClass = self.credentials.get_provider_class()
        
        self.rpc = ProviderClass.fetch_protected_resource(adapter=self.adapter,
                                                          url=self.url,
                                                          credentials=self.credentials,
                                                          content_parser=self.content_parser,
                                                          method=self.method,
                                                          response_parser=self.response_parser)
        
        return self
    
    def get_response(self):
        return self.rpc.get_response()










