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
    
    def fetch_oauth1(self, url, method, consumer_key, consumer_secret, access_token=None, access_token_secret=None):
        url = create_oauth1_url(url, access_token, access_token_secret, consumer_key, consumer_secret, method)
        return self.fetch_async(url, method).get_result()
    
    
    def get_current_url(self):
        """
        
        """
        
        raise NotImplementedError()
    
    
    def get_request_param(self, key):
        """
        
        """
        
        raise NotImplementedError()
    
    
    def set_phase(self, provider_name, phase):
        """
        
        """
        
        raise NotImplementedError()
    
    
    def get_phase(self, provider_name):
        """
        
        """
        
        raise NotImplementedError()
    
    
    def reset_phase(self, provider_name):
        """
        
        """
        
        raise NotImplementedError()
    
    
    def store_provider_data(self, provider_name, key, value):
        """
        
        """
        
        raise NotImplementedError()
    
    
    def retrieve_provider_data(self, provider_name, key, default=None):
        """
        
        """
        
        raise NotImplementedError()
    
    
    def get_providers_config(self):
        """
        
        """
        
        raise NotImplementedError()
    
    
    def redirect(self, uri):
        """
        
        """
        
        raise NotImplementedError()
    
    
    def fetch(self, method, url, params=None, headers=None):
        """
        
        """
        
        raise NotImplementedError()
    
    
    def fetch_async(self, url, method='GET'):
        """
        
        """
        
        raise NotImplementedError()
        
    
    @staticmethod
    def json_parser(body):
        """
        
        """
        
        raise NotImplementedError()
    
    
    @staticmethod
    def query_string_parser(body):
        """
        
        """
        
        raise NotImplementedError()
    
    
    def parse_response(self, response):
        """
        
        """
        
        raise NotImplementedError()


    
    