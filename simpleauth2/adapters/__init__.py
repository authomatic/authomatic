import simpleauth2
from urllib import urlencode
import binascii
import hashlib
import hmac
import random
import time
import urllib

def escape(s):
    """Escape a URL including any /."""
    return urllib.quote(s.encode('utf-8'), safe='~')


class BaseAdapter(object):
    """
    Base class for platform adapters
    
    Defines common interface for platform specific (non standard library) functionality.
    """    
    

    def login(self, provider_name, callback, scope=[]):
        
        providers_config = self.get_providers_config()
                
        # retrieve required settings for current provider and raise exceptions if missing
        provider_settings = providers_config.get(provider_name)
        if not provider_settings:
            raise simpleauth2.exceptions.ConfigError('Provider name "{}" not specified!'.format(provider_name))
        
        provider_class = provider_settings.get('class_name')
        if not provider_class:
            raise simpleauth2.exceptions.ConfigError('Class name not specified for provider {}!'.format(provider_name))
        
        consumer_key = provider_settings.get('consumer_key')
        if not consumer_key:
            raise simpleauth2.exceptions.ConfigError('Consumer key not specified for provider {}!'.format(provider_name))    
        
        consumer_secret = provider_settings.get('consumer_secret')
        if not consumer_secret:
            raise simpleauth2.exceptions.ConfigError('Consumer secret not specified for provider {}!'.format(provider_name))
        
        # merge scopes from config and argument
        scope = provider_settings.get('scope', []) + scope
        
        # create consumer
        consumer = simpleauth2.Consumer(consumer_key, consumer_secret, scope)
        
        # get phase
        phase = self.get_phase(provider_name)
        
        # store increased phase
        self.set_phase(provider_name, phase + 1)
        
            
        ProviderClass = simpleauth2.resolve_provider_class(provider_class)
        
        # instantiate and call provider class
        ProviderClass(self, phase, provider_name, consumer, callback, provider_settings.get('id')).login()
    
    
    def get_current_uri(self):
        """
        Returns the URI of current request without query parameters and fragment as string
        """
        
        raise NotImplementedError
    
    
    def get_request_param(self, key):
        """Returns the value of GET or POST variable of a request by key"""
        
        raise NotImplementedError
    
    
    def set_phase(self, provider_name, phase):
        """Saves the phase number so that it can be retrieved in another request"""
        
        raise NotImplementedError
    
    
    def get_phase(self, provider_name):
        """Retrieves the phase number saved in previous request"""
        
        raise NotImplementedError
    
    
    def reset_phase(self, provider_name):
        """Resets the phase to 0"""
        self.set_phase(provider_name, 0)
    
    
    def store_provider_data(self, provider_name, key, value):
        """Saves a key-value pair which can be retrieved in another request with the provider_name key"""
        
        raise NotImplementedError
    
    
    def retrieve_provider_data(self, provider_name, key, default=None):
        """Retrieves a key-value pair which was stored in previous request with the provider_name key"""
        
        raise NotImplementedError
    
    
    def get_providers_config(self):
        """
        Returns a dictionary like object with provider configuration
        
        The dictionary must have this structure:
        {
            'facebook': {
                'class_name': Facebook,
                'consumer_key': '###',
                'consumer_secret': '###',
                'scope': ['scope1', 'scope2', 'scope3']
            },
            'google': {
                'class_name': 'simpleauth2.providers.Google',
                'consumer_key': '###',
                'consumer_secret': '###',
                'scope': ['scope1', 'scope2', 'scope3']
            },
            'windows_live': {
                 'class_name': 'WindowsLive',
                 'consumer_key': '###',
                 'consumer_secret': '###',
                 'scope': ['scope1', 'scope2', 'scope3']
            }
        }
        """
        
        raise NotImplementedError
    
    
    def redirect(self, url):
        """Redirects to specified URL"""
        
        raise NotImplementedError
    
    
    def fetch(self, url, payload=None, method='GET', headers={}):
        """Fetches a url"""
        
        raise NotImplementedError
    
    
    def fetch_async(self, url, payload=None, method='GET', headers={}):
        """
        
        """
        
        raise NotImplementedError
        
    
    @staticmethod
    def json_parser(body):
        """
        
        """
        
        raise NotImplementedError
    
    
    @staticmethod
    def query_string_parser(body):
        """
        
        """
        
        raise NotImplementedError
    
    
    def parse_response(self, response):
        """
        
        """
        
        raise NotImplementedError


    
    