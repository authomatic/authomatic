from google.appengine.api import urlfetch
from google.appengine.ext import ndb
from simpleauth2 import Response, adapters
from urllib import urlencode
from webapp2_extras import sessions
import datetime
import logging
import openid
import urlparse


class GAEWebapp2AdapterError(Exception):
    pass


class ProviderConfig(ndb.Model):
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
        
        Returns a provider config dictionary
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
    def values(cls):
        # get all items
        results = cls.query().fetch()
        # return list of dictionaries
        return [result.to_dict() for result in results]
    
    
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
            example.short_name = 1
            example.put()
            
            raise GAEWebapp2AdapterError('A GAEWebapp2AdapterError data model was created!' + \
                                         'Go to {your_domain}/_ah/admin/datastore?kind=ProvidersConfigModel and populate it with data!')



class _GAESessionWrapper(adapters.BaseSession):
    
    def __init__(self, session, response):
        self.session = session
        self.response = response
    
    
    def __setitem__(self, key, value):
        self.session.__setitem__(key, value)
        self.session.container.save_session(self.response)    
        
    
    def __delitem__(self, key):
        self.session.__delitem__(key)
        self.session.container.save_session(self.response)
    
    
    def __getitem__(self, key):
        return self.session.__getitem__(key)
        
    
    def get(self, key):
        return self.session.get(key)
    
    
    def __getattr__(self, name):
        return getattr(self.session, name)
    


class GAEWebapp2Adapter(adapters.WebObBaseAdapter):
    
    request = None
    response = None
    session = None
    openid_store = None
    config = None
    
    def __init__(self, handler, config=None, session=None, session_secret=None,
                 session_key='simpleauth2', openid_store=openid.NDBOpenIDStore):
        
        self.request = handler.request
        self.response = handler.response
        
        self._handler = handler
        self._session_secret = session_secret
        self._session_key = session_key
        self.openid_store = openid_store
        
        if config:
            self.config = config
        else:
            self.config = ProviderConfig
            self.config.initialize()
        
        # create session
        if not (session or session_secret):
            raise Exception('Either session or session_secret must be specified')
        
        if not session:
            # create default session
            session_store = sessions.SessionStore(handler.request, dict(secret_key=session_secret))
            #FIXME: securecookie backend complains that <openid.yadis.manager.YadisServiceManager object at 0x9ea892c> is not JSON serializable
            session = session_store.get_session(session_key, max_age=60, backend='memcache')
        
        self.session = _GAESessionWrapper(session, self.response)
    
        
    def fetch_async(self, url, payload=None, method='GET', headers={}, response_parser=None, content_parser=None):
        """
        Makes an asynchronous call object
        """
        
        rpc = urlfetch.create_rpc()
        urlfetch.make_fetch_call(rpc, url, payload, method, headers)
        
        return adapters.RPC(rpc, response_parser or self.response_parser, content_parser)
    
    
    @staticmethod
    def response_parser(response, content_parser):
        return Response(status_code=response.status_code,
                        headers=response.headers,
                        content=response.content,
                        content_parser=content_parser)

