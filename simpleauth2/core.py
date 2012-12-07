"""
"""
from exceptions import ConfigError
import logging
from webapp2_extras import sessions

class Simpleauth2(object):
    def __init__(self, handler, providers, session_config):
        self._handler = handler
        self.providers = providers
        
        # create session
        self._session_store = sessions.SessionStore(self._handler.request, session_config)
        self._session = self._session_store.get_session('simpleauth2')
        
    def _save_sessions(self):
        self._session_store.save_sessions(self._handler.response)
    
    def _reset_phase(self):
        self._session[self.provider_name] = 0
    
    def _callback(self, event):
        # Set phase to 0
        self._reset_phase()
        
        # call user specified callback
        self.callback(event)
    
    def login(self, provider_name, callback):
        
        self.provider_name = provider_name
        self.callback = callback
        
        # get current phase from session
        self.phase = self._session.get(provider_name, 0)
        
        # increase phase in session
        self._session[provider_name] = self.phase + 1
                
        # retrieve required settings for current provider and raise exceptions if missing
        provider_settings = self.providers.get(provider_name)
        if not provider_settings:
            raise ConfigError('Provider name "{}" not specified!'.format(provider_name))
        
        ProviderClass = provider_settings.get('class')
        if not ProviderClass:
            raise ConfigError('Class not specified for provider {}!'.format(provider_name))
        
        self.consumer_id = provider_settings.get('id')
        if not self.consumer_id:
            raise ConfigError('ID not specified for provider {}!'.format(provider_name))    
        
        self.secret = provider_settings.get('secret')
        if not self.secret:
            raise ConfigError('Secret not specified for provider {}!'.format(provider_name))
        
        self.scope = provider_settings.get('scope')
        
        # recreate full current URI
        self.uri = self._handler.uri_for(self._handler.request.route.name, *self._handler.request.route_args, _full=True)
              
        # instantiate and call the service class
        ProviderClass(self)()
        
        # save sessions
        self._save_sessions()
    


