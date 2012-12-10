from exceptions import *
from simpleauth2.utils import Consumer
from webapp2_extras import sessions

def authenticate(provider_name, callback, handler, providers, session_config):
    
    # create session
    session_store = sessions.SessionStore(handler.request, session_config)
    session = session_store.get_session('simpleauth2', max_age=10)
    
    # get phase
    phase = session.get(provider_name, 0)
    
    # increase phase in session
    session[provider_name] = phase + 1
    
    # retrieve required settings for current provider and raise exceptions if missing
    provider_settings = providers.get(provider_name)
    if not provider_settings:
        raise ConfigError('Provider name "{}" not specified!'.format(provider_name))
    
    ProviderClass = provider_settings.get('class')
    if not ProviderClass:
        raise ConfigError('Class not specified for provider {}!'.format(provider_name))
    
    key = provider_settings.get('id')
    if not key:
        raise ConfigError('Consumer key not specified for provider {}!'.format(provider_name))    
    
    secret = provider_settings.get('secret')
    if not secret:
        raise ConfigError('Consumer secret not specified for provider {}!'.format(provider_name))
    
    scope = provider_settings.get('scope')
    
    consumer = Consumer(key, secret, scope)
    
    # instantiate and call provider class
    ProviderClass(phase, provider_name, consumer, handler, session, callback)()
    
    # save session
    session_store.save_sessions(handler.response)


