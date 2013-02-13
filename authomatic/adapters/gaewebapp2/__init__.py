from authomatic import adapters
from google.appengine.api import urlfetch
from google.appengine.ext import ndb
from urllib import urlencode
from webapp2_extras import sessions
import authomatic.core as core
import datetime
import logging
import pickle
import urlparse


class GAEWebapp2AdapterError(Exception):
    pass

#TODO: Move to separate module not tied to webapp2
#TODO: wrap to a function who returns initiates and returns this class.
class NDBConfig(ndb.Model):
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
            else:
                result_dict['scope'] = []
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
    
    JSON_SERIALIZABLE_KEY = 'json_serializable'
    
    def __init__(self, session, response):
        self.session = session
        self.response = response
    
    
    def _from_json_serializable(self, value):
        """
        Detects if value was created by self._save_json_serializable() and
        returns its original value if so or returns unchanged value.
        
        :param value:
        """
        
        if isinstance(value, dict) and value.get(self.JSON_SERIALIZABLE_KEY):
            return pickle.loads(value.get(self.JSON_SERIALIZABLE_KEY))
        else:
            return value
    
    
    def _save_json_serializable(self, key, value):
        """
        Converts non JSON serializable objects to {JSON_SERIALIZABLE_KEY, pickle.dumps(value)} dictionary.
        
        The securecookie session backend complains that YadisServiceManager is not JSON serializable.
        We go around this by pickling the value to a dictionary,
        which we can identify by the key for unpickling when retrieved from session.
        
        :param key:
        :param value:
        """
        
        try:
            self.session.__setitem__(key, value)
            self.session.container.save_session(self.response)
        except TypeError:
            # if value is not JSON serializable pickle it to a JSON serializable dictionary
            # with identifiable key.
            json_serializable = {self.JSON_SERIALIZABLE_KEY: pickle.dumps(value)}
            self.session.__setitem__(key, json_serializable)
            self.session.container.save_session(self.response)
    
    
    def __setitem__(self, key, value):
        self._save_json_serializable(key, value)
        
    
    def __delitem__(self, key):
        self.session.__delitem__(key)
        self.session.container.save_session(self.response)
    
    
    def __getitem__(self, key):
        return self._from_json_serializable(self.session.__getitem__(key))
        
    
    def get(self, key):
        return self._from_json_serializable(self.session.get(key))
    


class GAEWebapp2Adapter(adapters.WebObBaseAdapter):
    
    request = None
    response = None
    session = None
    
    def __init__(self, handler, session=None, session_secret=None,
                 session_key='authomatic', openid_store=None):
        
        self.request = handler.request
        self.response = handler.response
        
        self._handler = handler
        self._session_secret = session_secret
        self._session_key = session_key
        self._openid_store = openid_store
        
        # create session
        if not (session or session_secret):
            raise Exception('Either session or session_secret must be specified')
        
        if not session:
            # create default session
            session_store = sessions.SessionStore(handler.request, dict(secret_key=session_secret))
            session = session_store.get_session(session_key, max_age=60, backend='securecookie')
        
        self.session = _GAESessionWrapper(session, self.response)
    
        
    def fetch_async(self, url, payload=None, method='GET', headers={}, response_parser=None, content_parser=None):
        """
        Makes an asynchronous call object
        """
        
        rpc = urlfetch.create_rpc()
        urlfetch.make_fetch_call(rpc, url, payload, method, headers)
        
        return adapters.RPC(rpc, response_parser or self.response_parser, content_parser)
    
    
    @property
    def openid_store(self):
        if self._openid_store:
            return self._openid_store
        else:
            # import only if needed to avoid python-openid dependency if not neccessary
            from openid import NDBOpenIDStore
            return NDBOpenIDStore
    
    
    @staticmethod
    def response_parser(response, content_parser):
        return core.Response(status_code=response.status_code,
                        headers=response.headers,
                        content=response.content,
                        content_parser=content_parser)

