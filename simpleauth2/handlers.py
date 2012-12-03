"""
"""
from exceptions import ConfigError
import logging
import re

def auth_mixin_factory(services):
    """
    Returns ConfiguredAuthMixin class that adds support for OAuth 2.0, OAuth 1.0 and Open ID to webapp2.RequestHandler.
    
    Requires a base class with session support.
    """
    
    # Return properties with name-mingled name
    properties = dict(_AuthMixin__services=services)
    
    return type('ConfiguredAuthMixin', (_AuthMixin, ), properties)


class Auth(object):
    def __init__(self, handler, services):
        self.handler = handler
        self.services = services
    
    def login(self, service_name, callback):
        
        # check current phase by counting leading underscores of service_name
        phase = len(re.match(r'_*', service_name).group())
        
        # construct uri for next phase by adding another leading underscore
        next_phase_uri = self.handler.uri_for(self.handler.request.route.name, '_' + service_name, _full=True)
        
        # get rid of the underscores
        service_name = service_name[phase:]
        
        # retrieve required settings for current service and raise exceptions if missing
        service_settings = self.services.get(service_name)
        if not service_settings:
            raise ConfigError('Service {} not specified!'.format(service_name))
        
        service_class = service_settings.get('class')
        if not service_class:
            raise ConfigError('Class not specified for service {}!'.format(service_name))
        
        service_ID = service_settings.get('id')
        if not service_ID:
            raise ConfigError('ID not specified for service {}!'.format(service_name))    
        
        service_secret = service_settings.get('secret')
        if not service_secret:
            raise ConfigError('Secret not specified for service {}!'.format(service_name))
        
        # instantiate and call the service class
        service_class(phase=phase,
                      next_phase_uri=next_phase_uri,
                      ID=service_ID,
                      secret=service_secret,
                      handler=self.handler,
                      callback=callback,
                      service_name=service_name,
                      scope=service_settings.get('scope'))()

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
        if not hasattr(self, '_AuthMixin__simpleauth2'):
            # Make an Auth instance only if it doesn't exist yet
            self.__simpleauth2 = Auth(self, self._AuthMixin__services)
        return self.__simpleauth2
    
    


