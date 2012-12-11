from exceptions import *
from google.appengine.api import urlfetch
from urllib import urlencode
from webapp2_extras import sessions
import logging
import oauth2 as oauth1
import os
import urlparse
import webapp2
import models

# taken from anyjson.py
try:
    import simplejson as json
except ImportError: # pragma: no cover
    try:
        # Try to import from django, should work on App Engine
        from django.utils import simplejson as json
    except ImportError:
        # Should work for Python2.6 and higher.
        import json


def authenticate(provider_name, callback, handler, providers_config=None, session_secret=None, session=None, session_key='simpleauth2'):
    
    # use Providers model if no providers config specified
    if not providers_config:
        #models.initialize_providers_model()
        providers_config = models.Providers
        providers_config.initialize()
    
    # create session
    if not (session or session_secret):
        raise Exception('Either session or session_secret must be specified')
    
    if not session:
        # create default session
        session_store = sessions.SessionStore(handler.request, dict(secret_key=session_secret))
        session = session_store.get_session('simpleauth2', max_age=60)
    
    # session structure:
    #
    # {'facebook': {'phase': 0},
    #  'twitter': {'phase': 1,
    #              'oauth_token': None,
    #              'oauth_token_secret': None}}
        
    # retrieve required settings for current provider and raise exceptions if missing
    provider_settings = providers_config.get(provider_name)
    if not provider_settings:
        raise ConfigError('Provider name "{}" not specified!'.format(provider_name))
    
    ProviderClass = provider_settings.get('class_name')
    if not ProviderClass:
        raise ConfigError('Class name not specified for provider {}!'.format(provider_name))
    
    consumer_key = provider_settings.get('consumer_key')
    if not consumer_key:
        raise ConfigError('Consumer key not specified for provider {}!'.format(provider_name))    
    
    consumer_secret = provider_settings.get('consumer_secret')
    if not consumer_secret:
        raise ConfigError('Consumer secret not specified for provider {}!'.format(provider_name))
    
    scope = provider_settings.get('scope')
    
    # create consumer
    consumer = Consumer(consumer_key, consumer_secret, scope)
    
    # get phase
    phase = session.setdefault(session_key, {}).setdefault(provider_name, {}).setdefault('phase', 0)
    # increase phase in session
    session[session_key][provider_name]['phase'] = phase + 1    
    
    # resolve provider class passed as string
    if type(ProviderClass) in (str, unicode):
        # prepare path for simpleauth2.providers package
        path = '.'.join([__package__, 'providers', ProviderClass])
        # import from fully qualified path or from simpleauth2.providers package
        ProviderClass = webapp2.import_string(ProviderClass, True) or webapp2.import_string(path)
    
    # instantiate and call provider class
    ProviderClass(phase, provider_name, consumer, handler, session, session_key, callback)()
    
    # save session
    session_store.save_sessions(handler.response)



def json_parser(body):
    return json.loads(body)


def query_string_parser(body):
    res = dict(urlparse.parse_qsl(body))
    if not res:
        res = json_parser(body)
    return res


class Consumer(object):
    def __init__(self, key, secret, scope=None):
        self.key = key
        self.secret = secret
        self.scope = scope
        self.access_token = None


class User(object):
    def __init__(self, access_token, access_token_secret=None):
        self.access_token = access_token
        self.access_token_secret = access_token_secret


class Credentials(object):
    def __init__(self, access_token, access_token_secret=None, consumer_key=None, consumer_secret=None, expires=0, provider_type=None):
        self.access_token = access_token
        self.access_token_secret = access_token_secret
        self.consumer_key = consumer_key
        self.consumer_secret = consumer_secret
        self.expires = expires
        self.provider_type = provider_type


class AuthEvent(object):
    def __init__(self, provider, consumer, user, credentials):
        self.provider = provider
        self.consumer = consumer
        self.user = user
        self.credentials = credentials


class UserInfo(object):
    def __init__(self, *args, **kwargs):
        self.raw_user_info = kwargs.get('raw_user_info')
        self.ID = kwargs.get('id')
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


class FetchResult(object):
    """
    Provides unified interface to results of different http request types
    
    The interface resembles the google.appengine.api.urlfetch.fetch()
    """
    def __init__(self, response):
        
        if type(response) == urlfetch._URLFetchResult:
            # if request returned by google.appengine.api.urlfetch.fetch()
            self.content = response.content
            self.status_code = int(response.status_code)
            self.headers = response.headers
            self.final_url = response.final_url
            
        elif type(response) == tuple:
            # if request returned by oauth2.Client.request()
            self.headers = response[0]
            self.content = response[1]
            self.status_code = int(self.headers['status'])
            self.final_url = None
        
        self.data = json.loads(self.content)


def create_oauth1_url(base, access_token, access_token_secret, consumer_id, secret):
    token = oauth1.Token(access_token, access_token_secret)
    consumer = oauth1.Consumer(consumer_id, secret)
    client = oauth1.Client(consumer, token)
    
    request = oauth1.Request.from_consumer_and_token(consumer, token)
    request.url = base
    request.sign_request(client.method, consumer, token)
    
    params = urlencode(request)
    
    return base + '?' + params


def create_oauth2_url(base, access_token):
    return base + '?' + urlencode(dict(access_token=access_token))


class FetchRequest(object):
    def __init__(self, url, credentials, method='GET', parser=None):
        self.url = url
        self.credentials = credentials
        self.method = method
        self.parser = parser
        
        self.rpc = None
        
        if self.credentials.provider_type == 'OAuth2':
            self.url = create_oauth2_url(url, self.credentials.access_token)
        elif self.credentials.provider_type == 'OAuth1':
            self.url = create_oauth1_url(url,
                                         self.credentials.access_token,
                                         self.credentials.access_token_secret,
                                         self.credentials.consumer_key,
                                         self.credentials.consumer_secret)
    
    def fetch(self):
        self.rpc = urlfetch.create_rpc()
        urlfetch.make_fetch_call(self.rpc, self.url, method=self.method)
        return self
    
    def get_result(self):
        result = FetchResult(self.rpc.get_result())
        return self.parser(result) if self.parser else result

