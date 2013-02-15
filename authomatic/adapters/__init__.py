"""
Implement Adapters
------------------

Implementing an adapter for a Python web framework is easy.

You do it by subclassing the :class:`.BaseAdapter` abstract class.
There are only **nine** members that you need to implement and
the only complicated one is the :attr:`.BaseAdapter.openid_store`.

Moreover if your framework is based on the |webob|_ library
you can use the :class:`.WebObBaseAdapter` and you only need to
implement **three** members.

.. autoclass:: BaseAdapter
    :members:
    
.. autoclass:: WebObBaseAdapter
    :members:
    
.. autoclass:: AsynchronousFetch
    :members:
    
.. autoclass:: BaseSession
    :members: __setitem__, __getitem__, __delitem__, get
    :special-members:

"""

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
    """
    Interface for :attr:`.BaseAdapter.session`.
    """
    
    __metaclass__ = abc.ABCMeta
    
    @abc.abstractmethod
    def __setitem__(self, key, value):
        """
        Same as :attr:`dict.__setitem__`.
        
        :param key:
        :param value:
        """
    
    
    @abc.abstractmethod
    def __getitem__(self, key):
        """
        Same as :attr:`dict.__getitem__`.
        
        :param key:
        """
    
    
    @abc.abstractmethod
    def __delitem__(self, key):
        """
        Same as :attr:`dict.__delitem__`.
        
        :param key:
        """
    
    
    @abc.abstractmethod
    def get(self, key):
        """
        Same as :attr:`dict.get`.
        
        :param key:
        """


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


class AsynchronousFetch(object):
    """
    Represents an asynchronous URL fetch call.
    """
    
    def __init__(self, rpc_object, adapter, response_parser, content_parser):
        """
        :param rpc_object:
            Any object that has a get_result() method.
        
        :param adapter:
            The adapter instance.
        
        :param function response_parser:
            The :meth:`.BaseAdapter.response_parser`.
            
        :param function content_parser:
            Should be passed to the :class:`.AsynchronousFetch` constructor.
        """
        
        self.rpc_object = rpc_object
        self.response_parser = response_parser or adapter.response_parser
        self.content_parser = content_parser
    
    def get_response(self):
        """
        Returns Response instance
        """
        
        return self.response_parser(self.rpc_object.get_result(), self.content_parser)


class BaseAdapter(object):
    """
    Base class for platform adapters
    
    Defines common interface for platform specific non standard library functionality.
    """    
    
    __metaclass__ = abc.ABCMeta
    
    
    @abc.abstractproperty
    def url(self):
        """
        Must return the url of the actual request including path but without query and fragment
        
        :returns:
            :class:`str`
        """
    
    
    @abc.abstractproperty
    def params(self):
        """
        Must return a dictionary of all request parameters of any HTTP method.
        
        :returns:
            :class:`dict`
        """
    
    
    @abc.abstractmethod
    def write(self, value):
        """
        Must write specified value to response.
        
        :param str value:
            String to be written to response.
        
        :returns:
            :class:`dict`
        """
    
    
    @abc.abstractmethod
    def set_header(self, key, value):
        """
        Must set response headers to ``Key: value``.
        
        :param str key:
            Header name.
            
        :param str value:
            Header value.
        """
    
    
    @abc.abstractmethod
    def redirect(self, url):
        """
        Must issue a http 302 redirect to a specified URL.
        
        :param str url:
            URL to be redirected to.
        """
    
    
    @abc.abstractproperty
    def session(self):
        """
        A session object with :class:`.BaseSession` or :class:`dict` interface.
        
        :returns:
            Session dictionary.
        """
    
    
    @abc.abstractmethod
    def response_parser(self, response, content_parser):
        """
        Must convert platform specific URL fetch response to :class:`.core.Response`.
        
        .. warning:: |classmethod|
        
        :param response:
            Result of platform specific URL fetch call.
        
        :param function content_parser:
            should be passed to :class:`.core.Response` constructor.
        
        :returns:
            :class:`.core.Response`
        """
    
    
    @abc.abstractproperty
    def openid_store(self):
        """
        A permanent storage abstraction with :class:`openid.store.interface.OpenIDStore` interface
        of the `python-openid`_ library.
        
        .. note::
            
            Required only by the :class:`.OpenID` provider so it is a good idea to use **conditional import**.
        
        :returns:
            An object with the :class:`openid.store.interface.OpenIDStore` interface.
        """
    
    
    @abc.abstractmethod
    def fetch_async(self, url, payload=None, method='GET', headers={}, response_parser=None, content_parser=None):    
        """
        Must return an instance of the :class:`.AsynchronousFetch` class.
        
        .. note::
            
            If your framework doesn't support asynchronous calls do it like this:
            ::
                
                def fetch_async(self, url, payload=None, method='GET',headers={},
                                response_parser=None, content_parser=None):
                    
                    # A dummy rpc object
                    rpc = lambda: None
                    # Make the synchronous fetch on the get_result() call.
                    rpc.get_result = lambda: your_framework.fetch()
                    
                    return adapters.AsynchronousFetch(rpc, self, response_parser, content_parser)
                
        
        :param str url:
            URL to fetch.
            
        :param str payload:
            Body of the request.
            
        :param str method:
            HTTP method of the request.
            
        :param dict headers:
            Dictionary of HTTP headers of the request.
            
        :param function response_parser:
            The :meth:`.response_parser`. Should be passed to the :class:`.AsynchronousFetch` constructor.
            
        :param function content_parser:
            Should be passed to the :class:`.AsynchronousFetch` constructor.
            
        :returns:
            :class:`.AsynchronousFetch`
        """


class WebObBaseAdapter(BaseAdapter):
    """
    Abstract base class for adapters for |webob|_ based frameworks.
    
    If you use this base class you only need to implement these three :class:`.BaseAdapter` members:
    
    * :meth:`.BaseAdapter.fetch_async`
    * :meth:`.BaseAdapter.response_parser`
    * :attr:`.BaseAdapter.openid_store`
    
    """
    
    @abc.abstractproperty
    def request(self):
        """
        Must be a |webob|_ :class:`Request`.
        """
    
    
    @abc.abstractproperty
    def response(self):
        """
       Must be a |webob|_ :class:`Response`.
        """
    
    
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
    
    
