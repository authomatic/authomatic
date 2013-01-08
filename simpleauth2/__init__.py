from exceptions import *
from urllib import urlencode
import datetime
import sys


def login(adapter, provider_name, callback, scope=[]):
    
    providers_config = adapter.get_providers_config()
            
    # retrieve required settings for current provider and raise exceptions if missing
    provider_settings = providers_config.get(provider_name)
    if not provider_settings:
        raise ConfigError('Provider name "{}" not specified!'.format(provider_name))
    
    provider_class = provider_settings.get('class_name')
    if not provider_class:
        raise ConfigError('Class name not specified for provider {}!'.format(provider_name))
    
    consumer_key = provider_settings.get('consumer_key')
    if not consumer_key:
        raise ConfigError('Consumer key not specified for provider {}!'.format(provider_name))    
    
    consumer_secret = provider_settings.get('consumer_secret')
    if not consumer_secret:
        raise ConfigError('Consumer secret not specified for provider {}!'.format(provider_name))
    
    # merge scopes from config and argument
    scope.extend(provider_settings.get('scope', []))
    
    # create consumer
    consumer = Consumer(consumer_key, consumer_secret, scope)
    
    # get phase
    phase = adapter.get_phase(provider_name)
    
    # store increased phase
    adapter.set_phase(provider_name, phase + 1)
    
        
    ProviderClass = resolve_provider_class(provider_class)
    
    # instantiate and call provider class
    ProviderClass(adapter, phase, provider_name, consumer, callback).login()


def resolve_provider_class(class_):
    if type(class_) in (str, unicode):
        # prepare path for simpleauth2.providers package
        path = '.'.join([__package__, 'providers', class_])        
        return import_string(path)        
    else:
        return class_


def import_string(import_name):
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
        raise ImportStringError(import_name, e), None, sys.exc_info()[2]


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
    def __init__(self, access_token, access_token_secret=None, consumer_key=None, consumer_secret=None, expires_in=0, provider_type=None):
        self.access_token = access_token
        self.access_token_secret = access_token_secret
        self.consumer_key = consumer_key
        self.consumer_secret = consumer_secret
        self.provider_type = provider_type
        self._expires_in = expires_in
        self._set_expiration_date(expires_in)
    
    
    def _set_expiration_date(self, expires_in):
        if expires_in:
            self.expiration_date = datetime.datetime.now() + datetime.timedelta(seconds=int(expires_in))
        else:
            self.expiration_date = None
    
    
    @property
    def expires_in(self): pass
    
    
    @expires_in.getter
    def expires_in(self): 
        return self._expires_in
    
    
    @expires_in.setter
    def expires_in(self, value):
        # update expiration_date 
        self._set_expiration_date(value)
        
        self._expires_in = value


class AuthEvent(object):
    def __init__(self, provider, consumer, user, credentials):
        self.provider = provider
        self.consumer = consumer
        self.user = user
        self.credentials = credentials


class Response(object):
    """
    Provides unified interface to results of different http request types
    """
    
    def __init__(self, **kwargs):
        
        self.content = kwargs.get('content')
        self.status_code = kwargs.get('status_code')
        self.headers = kwargs.get('headers')
        self.final_url = kwargs.get('final_url')
        self.data = kwargs.get('data')


class Request(object):
    def __init__(self, adapter, url, credentials, method='GET', parser=None):
        self.adapter = adapter
        self.url = url
        self.credentials = credentials
        self.method = method
        self.parser = parser
        
        self.rpc = None
        
        if self.credentials.provider_type == 'OAuth2':
            self.url = self.adapter.create_oauth2_url(url, self.credentials.access_token)
        elif self.credentials.provider_type == 'OAuth1':
            self.url = self.adapter.create_oauth1_url(url,
                                         self.credentials.access_token,
                                         self.credentials.access_token_secret,
                                         self.credentials.consumer_key,
                                         self.credentials.consumer_secret)
    
    def fetch(self):
        self.rpc = self.adapter.fetch_async(self.url, self.method)        
        return self
    
    def get_result(self):
        result_dict = self.adapter.normalize_response(self.rpc.get_result())
        result = Response(**result_dict)
        return self.parser(result) if self.parser else result

