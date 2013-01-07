from . import BaseAdapter
from google.appengine.api import urlfetch
from google.appengine.ext import ndb
from urllib import urlencode
from webapp2_extras import sessions
import logging
import oauth2 as oauth1
import urlparse
import webapp2

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

class ProvidersConfigModel(ndb.Model):
    """
    Datastore model for providers configuration
    """
    
    name = ndb.StringProperty()
    class_name = ndb.StringProperty()
    consumer_key = ndb.StringProperty()
    consumer_secret = ndb.StringProperty()
    scope = ndb.StringProperty()
    
    @classmethod
    def get(cls, key, default=None):
        """
        Resembles the dict.get(key[, default=None]) method
        
        Returns the 
        """
        result = cls.query(cls.name == key).get()
        if result:
            result_dict = result.to_dict()
            # convert scope to list
            scope = result_dict.get('scope')
            if scope:
                result_dict['scope'] = [s.strip() for s in scope.split(',')]
            logging.info('Providers.scope = {}'.format(result_dict['scope']))
            return result_dict
        else:
            return default 
        
    @classmethod
    def initialize(cls):
        """
        Creates an Example entity if the model is empty
        """
        
        if not len(cls.query().fetch()):
            example = cls.get_or_insert('Example')
            example.name = 'string-identifier-of-provider.'
            example.class_name = 'Name of provider class.'
            example.consumer_key = 'Consumer key.'
            example.consumer_secret = 'Consumer secret'
            example.scope = 'coma, separated, list, of, scopes'
            example.put()


class GAEWebapp2Adapter(BaseAdapter):
    
    def __init__(self, handler, providers_config=None, session=None, session_secret=None, session_key='simpleauth2'):
        self._handler = handler
        self._providers_config = providers_config
        self._session = session
        self._session_secret = session_secret
        self._session_key = session_key
        
        # create session
        if not (session or session_secret):
            raise Exception('Either session or session_secret must be specified')
        
        if not session:
            # create default session
            session_store = sessions.SessionStore(handler.request, dict(secret_key=session_secret))
            self._session = session_store.get_session(session_key, max_age=60)
        
        # session structure:
        #
        # {'facebook': {'phase': 0},
        #  'twitter': {'phase': 1,
        #              'oauth_token': None,
        #              'oauth_token_secret': None}}
    
    
    def get_current_url(self):
        """
        Returns the url of the actual request
        """
        route_name = self._handler.request.route.name
        args = self._handler.request.route_args
        return self._handler.uri_for(route_name, *args, _full=True)
    
    
    def get_request_param(self, key):
        """
        Returns a GET or POST variable by key
        """
        return self._handler.request.params.get(key)
    
    
    def set_phase(self, provider_name, phase):
        self.store_provider_data(provider_name, 'phase', phase)
    
    
    def get_phase(self, provider_name):
        return self.retrieve_provider_data(provider_name, 'phase', 0)
    
    
    def reset_phase(self, provider_name):
        self.set_phase(provider_name, 0)
    
    
    def store_provider_data(self, provider_name, key, value):
        self._session.setdefault(self._session_key, {}).setdefault(provider_name, {})[key] = value
        self._save_session()
        
        
    def retrieve_provider_data(self, provider_name, key, default=None):
        return self._session.setdefault(self._session_key, {}).setdefault(provider_name, {}).get(key, default)
    
    
    def get_providers_config(self):
        
        if self._providers_config:
            return self._providers_config
        else:
            # use Providers model if no providers config specified
            providers_config = ProvidersConfigModel
            providers_config.initialize()
            return providers_config
    
    
    def redirect(self, uri):
        self._handler.redirect(uri)
    
    
    def fetch(self, method, url, params=None, headers=None):
        #TODO: Check whether the method is valid
        return urlfetch.fetch(url, params, method=method, headers=headers)
    
    
    def fetch_async(self, url, method='GET'):
        """
        Makes an asynchronous object
        
        Must return an object which has a get_result() method
        """
        
        rpc = urlfetch.create_rpc()
        urlfetch.make_fetch_call(rpc, url, method=method)
        return rpc
    
    
    def fetch_oauth1(self, method, url, consumer_key, consumer_secret, access_token=None, access_token_secret=None):
        # Create token only if needed
        token = oauth1.Token(access_token, access_token_secret) if access_token and access_token_secret else None
        consumer = oauth1.Consumer(consumer_key, consumer_secret)
        client = oauth1.Client(consumer, token)
        
        # make request and return response
        return client.request(url, method)
    
    
    @staticmethod
    def json_parser(body):
        return json.loads(body)
    
    
    @staticmethod
    def query_string_parser(body):
        res = dict(urlparse.parse_qsl(body))
        if not res:
            res = json.loads(body)
        return res
    
    
    def create_oauth1_url(self, url, access_token, access_token_secret, consumer_key, consumer_secret):
        token = oauth1.Token(access_token, access_token_secret)
        consumer = oauth1.Consumer(consumer_key, consumer_secret)
        client = oauth1.Client(consumer, token)
        
        request = oauth1.Request.from_consumer_and_token(consumer, token)
        request.url = url
        request.sign_request(client.method, consumer, token)
        
        params = urlencode(request)
        
        return url + '?' + params
    
    
    def normalize_response(self, response):
        
        res = {}
        
        if type(response) == urlfetch._URLFetchResult:
            # if request returned by google.appengine.api.urlfetch.fetch()
            res['status_code'] = int(response.status_code)
            res['headers'] = response.headers
            res['content'] = response.content
            res['final_url'] = response.final_url
            
        elif type(response) == tuple:
            # if request returned by oauth2.Client.request()
            res['headers'] = response[0]
            res['status_code'] = int(response[0].get('status'))            
            res['content'] = response[1]
            res['final_url'] = None
        
        res['data'] = json.loads(res['content'])
        
        return res
    
    
    def resolve_class(self, class_):
        # resolve provider class passed as string
        if type(class_) in (str, unicode):
            # prepare path for simpleauth2.providers package
            path = '.'.join([__package__, 'providers', class_])
            # import from fully qualified path or from simpleauth2.providers package
            return webapp2.import_string(class_, True) or webapp2.import_string(path)
        else:
            return class_
    
    def create_oauth2_url(self, url, access_token):
        return url + '?' + urlencode(dict(access_token=access_token))
    
    
    def _save_session(self):
        self._session.container.session_store.save_sessions(self._handler.response)

