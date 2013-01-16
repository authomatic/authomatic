from . import BaseAdapter
from google.appengine.api import urlfetch
from google.appengine.ext import ndb
from openid import association
from openid.store import interface
from simpleauth2 import Response, RPC
from urllib import urlencode
from webapp2_extras import sessions
import datetime
import urlparse

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
    short_name = ndb.IntegerProperty()
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

#TODO: Move to separate module and pass it to the constructor of GAEWebapp2Adapter
class NDBOpenIDStore(ndb.Model, interface.OpenIDStore):
    serialized = ndb.StringProperty()
    expiration_date = ndb.DateTimeProperty()
    # we need issued to sort by most recently issued
    issued = ndb.IntegerProperty()
    
    
    @classmethod
    def storeAssociation(cls, server_url, association):
        # store an entity with key = server_url
                
        issued = datetime.datetime.fromtimestamp(association.issued)
        lifetime = datetime.timedelta(0, association.lifetime)
        
        expiration_date = issued + lifetime
        
        entity = cls.get_or_insert(association.handle, parent=ndb.Key('ServerUrl', server_url))
        
        entity.serialized = association.serialize()
        entity.expiration_date = expiration_date
        entity.issued = association.issued
        entity.put()
    
    
    @classmethod
    def _delete_expired(cls):
        
        #TODO: Maybe it could be better as a background task
        
        # query for all expired
        query = cls.query(cls.expiration_date <= datetime.datetime.now())
        
        # fetch keys only
        expired = query.fetch(keys_only=True)
        
        # delete all expired
        ndb.delete_multi(expired)
    
    
    @classmethod
    def getAssociation(cls, server_url, handle=None):
        
        cls._delete_expired()
        
        if handle:
            key = ndb.Key('ServerUrl', server_url, cls, handle)
            entity = key.get()
        else:
            # return most recently issued association
            entity = cls.query(ancestor=ndb.Key('ServerUrl', server_url)).order(-cls.issued).get()
        
        if entity:
            return association.Association.deserialize(entity.serialized)


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
    
    def get_current_uri(self):
        """Returns the uri of the actual request"""
        
        route_name = self._handler.request.route.name
        args = self._handler.request.route_args
        return self._handler.uri_for(route_name, *args, _full=True)
    
    
    def get_request_param(self, key):
        """Returns a GET or POST variable by key"""
        
        return self._handler.request.params.get(key)
    
    
    def set_phase(self, provider_name, phase):
        self.store_provider_data(provider_name, 'phase', phase)
    
    
    def get_phase(self, provider_name):
        return self.retrieve_provider_data(provider_name, 'phase', 0)
    
    
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
    
    
    def redirect(self, url):
        self._handler.redirect(url)
    
    
    def fetch_async(self, content_parser, url, params={}, method='GET', headers={}, response_parser=None):
        """
        Makes an asynchronous object
        
        Must return an object which has a get_result() method
        """
        
        rpc = urlfetch.create_rpc()
        urlfetch.make_fetch_call(rpc, url, urlencode(params), method, headers)
        
        return RPC(rpc, response_parser or self.response_parser, content_parser)
    
    
    @staticmethod
    def json_parser(body):
        return json.loads(body)
    
    
    @staticmethod
    def query_string_parser(body):
        res = dict(urlparse.parse_qsl(body))
        if not res:
            try:
                res = json.loads(body) if body else None
            except:
                pass
        return res
    
    
    @staticmethod
    def response_parser(response, content_parser):
        resp = Response(content_parser)
        
        resp.content = response.content
        resp.status_code = response.status_code
        resp.headers = response.headers
        
        return resp
    
    
    @staticmethod
    def get_openid_store():
        return NDBOpenIDStore()
    
    
    def _save_session(self):
        self._session.container.session_store.save_sessions(self._handler.response)

