"""
"""
from exceptions import ConfigError
import logging
import re
from webapp2_extras import sessions

def auth_mixin_factory(services, session_config):
    """
    Returns ConfiguredAuthMixin class that adds support for OAuth 2.0, OAuth 1.0 and Open ID to webapp2.RequestHandler.
    
    Requires a base class with session support.
    """
    
    # Return properties with name-mingled name
    properties = dict(_AuthMixin__services=services,
                      _AuthMixin__session_config=session_config)
    
    return type('ConfiguredAuthMixin', (_AuthMixin, ), properties)


class Simpleauth2(object):
    def __init__(self, handler, services, session_config):
        self._handler = handler
        self.services = services
        
        # create session
        self._session_store = sessions.SessionStore(self._handler.request, session_config)
        self._session = self._session_store.get_session('simpleauth2')
        
    def _save_sessions(self):
        self._session_store.save_sessions(self._handler.response)
    
    def _reset_phase(self):
        self._session[self.service_name] = 0
    
    def _callback(self, event):
        # Set phase to 0
        self._reset_phase()
        
        # call user specified callback
        self.callback(event)
    
    def login(self, service_name, callback):
        
        self.service_name = service_name
        self.callback = callback
        
        # get current phase from session
        self.phase = self._session.get(service_name, 0)
        
        # increase phase in session
        self._session[service_name] = self.phase + 1
                
        # retrieve required settings for current service and raise exceptions if missing
        service_settings = self.services.get(service_name)
        if not service_settings:
            raise ConfigError('Service {} not specified!'.format(service_name))
        
        service_class = service_settings.get('class')
        if not service_class:
            raise ConfigError('Class not specified for service {}!'.format(service_name))
        
        self.service_ID = service_settings.get('id')
        if not self.service_ID:
            raise ConfigError('ID not specified for service {}!'.format(service_name))    
        
        self.secret = service_settings.get('secret')
        if not self.secret:
            raise ConfigError('Secret not specified for service {}!'.format(service_name))
        
        self.scope = service_settings.get('scope')
        
        # recreate full current URI
        self.uri = self._handler.uri_for(self._handler.request.route.name, *self._handler.request.route_args, _full=True)
                
        # instantiate and call the service class
        service_class(service_name, self)()
        
        # save sessions
        self._save_sessions()

class _AuthMixin(object):
    """
    Base class for ConfiguredAuthMixin
    
    Do not use this mixin directly! You should use the auth_mixin_factory(services) function
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
            self.__simpleauth2 = Simpleauth2(self, self.__services, self.__session_config)
            
        return self.__simpleauth2
    


