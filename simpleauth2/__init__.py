from exceptions import *
from simpleauth2.utils import Consumer
from webapp2_extras import sessions
import logging

def authenticate(provider_name, callback, handler, providers, session_secret=None, session=None, session_key='simpleauth2'):
    
    # create session
    if not (session or session_secret):
        raise Exception('Either session or session_secret must be specified')
    
    if not session:
        # create default session
        session_store = sessions.SessionStore(handler.request, dict(secret_key=session_secret))
        session = session_store.get_session('simpleauth2', max_age=60)
    
    # session structure:
    #
    # {'facebook': {'phase': 0},
    #  'twitter': {'phase': 1,
    #              'oauth_token': None,
    #              'oauth_token_secret': None}}
        
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
    
    # create consumer
    consumer = Consumer(key, secret, scope)
    
    # get phase
    phase = session.setdefault(session_key, {}).setdefault(provider_name, {}).setdefault('phase', 0)
    # increase phase in session
    session[session_key][provider_name]['phase'] = phase + 1
    
    # instantiate and call provider class
    ProviderClass(phase, provider_name, consumer, handler, session, session_key, callback)()
    
    # save session
    session_store.save_sessions(handler.response)


