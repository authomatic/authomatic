from . import BaseAdapter
from google.appengine.ext import ndb
from webapp2_extras import sessions
import logging

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
        
        
    def set_phase(self, provider_name, phase):
        self._session[self._session_key][provider_name]['phase'] = phase 
        self._save_session()
    
    def get_phase(self, provider_name):
        return self._session.setdefault(self._session_key, {}).setdefault(provider_name, {}).setdefault('phase', 0)
    
    def get_providers_config(self):
        
        if self._providers_config:
            return self._providers_config
        else:
            # use Providers model if no providers config specified
            providers_config = ProvidersConfigModel
            providers_config.initialize()
            return providers_config
    
    def _save_session(self):
        self._session.container.session_store.save_sessions(self._handler.response)

