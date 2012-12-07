"""
"""
from exceptions import ConfigError
import logging
from webapp2_extras import sessions

def auth_mixin_factory(providers, session_config):
    """
    Returns ConfiguredAuthMixin class that adds support for OAuth 2.0, OAuth 1.0 and Open ID to webapp2.RequestHandler.
    
    Requires a base class with session support.
    """
    
    # Return properties with name-mingled name
    properties = dict(_AuthMixin__providers=providers,
                      _AuthMixin__session_config=session_config)
    
    return type('ConfiguredAuthMixin', (_AuthMixin, ), properties)

class _AuthMixin(object):
    """
    Base class for ConfiguredAuthMixin
    
    Do not use this mixin directly! You should use the auth_mixin_factory(providers) function
    The mixin only adds the "auth" attribute to the subclass.
    """
    
    # We need to pass an instance of the Request Handler to the Auth class, but we cannot use
    # constructor here because it will not be called unless the mixin is the first base class
    # We use a trick with a getter instead.
    @property
    def simpleauth2(self):
        pass
    
    @simpleauth2.getter
    def simpleauth2(self):
        # Make an Auth instance only if it doesn't exist yet
        if not hasattr(self, '_AuthMixin__simpleauth2'):
            self.__simpleauth2 = Simpleauth2(self, self.__providers, self.__session_config)
            
        return self.__simpleauth2


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
    


