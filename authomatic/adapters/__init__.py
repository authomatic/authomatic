from urllib import urlencode
import binascii
import hashlib
import hmac
import random
import authomatic
import time
import urllib
from _pyio import __metaclass__
import abc


class BaseSession(object):
    
    __metaclass__ = abc.ABCMeta
    
    @abc.abstractmethod
    def __setitem__(self, key, value):
        pass
    
    
    @abc.abstractmethod
    def __getitem__(self, key):
        pass
    
    
    @abc.abstractmethod
    def __delitem__(self, key):
        pass
    
    
    @abc.abstractmethod
    def get(self, key):
        pass


class BaseConfig(object):
    
    __metaclass__ = abc.ABCMeta
    
    @abc.abstractmethod
    def get(self, key):
        """
        
        :param key:
        """
    
    @abc.abstractmethod
    def values(self):
        """
        
        """        


class RPC(object):
    """
    Remote Procedure Call wrapper
    """
    
    def __init__(self, rpc_object, response_parser, content_parser):
        """
        
        
        :param rpc_object: Any object that has a get_result() method.
        :param response_parser: 
        :param content_parser:
        """
        
        self.rpc_object = rpc_object
        self.response_parser = response_parser
        self.content_parser = content_parser
    
    def get_response(self):
        """
        Returns Response instance
        """
        
        return self.response_parser(self.rpc_object.get_result(), self.content_parser)


class BaseAdapter(object):
    """
    Base class for platform adapters
    
    Defines common interface for platform specific (non standard library) functionality.
    """    
    
    __metaclass__ = abc.ABCMeta
    
    def login(self, *args, **kwargs):
        return authomatic.login(self,  *args, **kwargs)
    
    
    def config(self):
        """
        Any object that has the get('provider-name') method which should return
        a provider config dictionary.
        
        Ment to provide an alternative to a hardcoded config, i.e. Data model config. 
        
        TODO: point to config section of future documentation? 
        """
        
        return None
    
    
    @abc.abstractproperty
    def url(self):
        """Must return the url of the actual request including path but without query and fragment"""
    
    
    @abc.abstractproperty
    def params(self):
        """Must return a dictionary of all request parameters of any HTTP method."""
    
    
    @abc.abstractmethod
    def write(self, value):
        """
        Must write specified value to response.
        
        :param value: string
        """
    
    
    @abc.abstractmethod
    def set_header(self, key, value):
        """
        Must set response headers to key = value.
        
        :param key:
        :param value:
        """
    
    
    @abc.abstractmethod
    def redirect(self, url):
        """
        Must issue a http 302 redirect to the url
        
        :param url: string
        """
    
    
    @abc.abstractproperty
    def session(self):
        """
        A session abstraction with BaseSession or dict interface
        """
    
    
    @abc.abstractmethod
    def response_parser(self, response, content_parser):
        """
        A classproperty to convert platform specific fetch response to authomatic.Response.
        
        Must be staticmethod!
        
        :param response: result of platform specific fetch call
        :param content_parser: should be passed to authomatic.Response constructor.
        
        :returns: authomatic.Response
        """
    
    
    @abc.abstractproperty
    def openid_store(self):
        """
        A permanent storage abstraction as described by the openid.store.interface.OpenIDStore interface
        of the python-openid library http://pypi.python.org/pypi/python-openid/.
        
        Required only by the OpenID provider
        """
    
    
    @abc.abstractmethod
    def fetch_async(self, url, payload=None, method='GET', headers={}, response_parser=None, content_parser=None):    
        """
        Must return an instance of the RPC class.
        
        :param url:
        :param payload:
        :param method:
        :param headers:
        :param response_parser:
        :param content_parser:
        """


class WebObBaseAdapter(BaseAdapter):
    """
    Abstract base class for adapters for WebOb based frameworks.
    
    See http://webob.org/
    """
    
    @abc.abstractproperty
    def request(self):
        pass
    
    
    @abc.abstractproperty
    def response(self):
        pass
    
    
    #===========================================================================
    # Request
    #===========================================================================
    
    @property
    def url(self):
        return self.request.path_url
    
    
    @property
    def params(self):
        return dict(self.request.params)
    
    
    #===========================================================================
    # Response
    #===========================================================================
            
    def write(self, value):
        self.response.write(value)
    
    
    def set_header(self, key, value):
        self.response.headers[key] = value
    
    
    def redirect(self, url):
        self.response.location = url
        self.response.status = 302
    
    
    
    
    

























