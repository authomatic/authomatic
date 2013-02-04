from google.appengine.api import urlfetch
from google.appengine.ext import ndb
from simpleauth2 import Response, adapters
from urllib import urlencode
from webapp2_extras import sessions
import openid
import datetime
import urlparse


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


class GAEWebapp2AdapterError(Exception):
    pass


class _GAESessionWrapper(adapters.BaseSession):
    
    def __init__(self, session, response):
        self.session = session
        self.response = response
    
    
    def __setitem__(self, key, value):
        self.session.__setitem__(key, value)
        # we need to save the session store
        # it is actually the only reason why we need this wrapper
        self.session.container.save_session(self.response)
    
    def __getitem__(self, key):
        return self.session.__getitem__(key)
    
    
    def __delitem__(self, key):
        return self.session.__delitem__(key)
    
    
    def get(self, key):
        return self.session.get(key)
    


class GAEWebapp2Adapter(adapters.WebObBaseAdapter):
    
    request = None
    response = None
    session = None
    openid_store = None
    
    def __init__(self, handler, providers_config=None, session=None,
                 session_secret=None, session_key='simpleauth2', openid_store=openid.NDBOpenIDStore):
        
        self.request = handler.request
        self.response = handler.response
        
        self._handler = handler
        self._config = providers_config
        self._session_secret = session_secret
        self._session_key = session_key
        self.openid_store = openid_store
        
        # create session
        if not (session or session_secret):
            raise Exception('Either session or session_secret must be specified')
        
        if not session:
            # create default session
            session_store = sessions.SessionStore(handler.request, dict(secret_key=session_secret))
            #FIXME: securecookie backend complains that <openid.yadis.manager.YadisServiceManager object at 0x9ea892c> is not JSON serializable
            session = session_store.get_session(session_key, max_age=60, backend='memcache')
        
        self.session = _GAESessionWrapper(session, self.response)
    
    
    #TODO: Make config optional by adapters
    @property
    def config(self):
        if self._config:
            return self._config
        else:
            # use Providers model if no providers config specified
            providers_config = ProvidersConfigModel
            providers_config.initialize()
            return providers_config
    
        
    def fetch_async(self, url, payload=None, method='GET', headers={}, response_parser=None, content_parser=None):
        """
        Makes an asynchronous call object
        
        Must return an object which has a get_result() method
        """
                
        
        rpc = urlfetch.create_rpc()
        urlfetch.make_fetch_call(rpc, url, payload, method, headers)
        
        #TODO: Redundant???
        return adapters.RPC(rpc, response_parser or self.response_parser, content_parser)
    
    
    @staticmethod
    def response_parser(response, content_parser):
        resp = Response(content_parser)
        
        resp.content = response.content
        resp.status_code = response.status_code
        resp.headers = response.headers
        
        return resp

