from simpleauth2 import create_oauth1_url
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
    
    #TODO: Get rid of it, move it to provider
    def fetch_oauth1(self, content_parser, url, method, consumer_key, consumer_secret, access_token=None, access_token_secret=None):
        url = create_oauth1_url(url, access_token, access_token_secret, consumer_key, consumer_secret, method)
        return self.fetch_async(content_parser, url, method).get_result()
    
    
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


    
    