# -*- coding: utf-8 -*-
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

from _pyio import __metaclass__
from urllib import urlencode
import abc
import authomatic
import binascii
import hashlib
import hmac
import logging
import random
import time
import urllib


class BaseAdapter(object):
    """
    Base class for platform adapters
    
    Defines common interface for WSGI framework specific functionality.
    """    
    
    __metaclass__ = abc.ABCMeta
    
    
    @abc.abstractmethod
    def write(self, value):
        """
        Must write specified value to response.
        
        :param str value:
            String to be written to response.
        
        :returns:
            :class:`dict`
        """
    
    
    @abc.abstractproperty
    def params(self):
        """
        Must return a dictionary of all request parameters of any HTTP method.
        
        :returns:
            :class:`dict`
        """
    
    
    @abc.abstractproperty
    def url(self):
        """
        Must return the url of the actual request including path but without query and fragment
        
        :returns:
            :class:`str`
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
    
    
    @abc.abstractproperty
    def headers(self):
        """
        We need it to retrieve the session cookie.
        """
    
    
    @abc.abstractproperty
    def cookies(self):
        """
        We need it to retrieve the session cookie.
        """
    
    
    @abc.abstractmethod
    def set_status(self):
        """
        To set the staus in JSON endpoint.
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
    
    @property
    def headers(self):
        return dict(self.request.headers)
    
    @property
    def cookies(self):
        return dict(self.request.cookies)
    
    
    #===========================================================================
    # Response
    #===========================================================================
            
    def write(self, value):
        self.response.write(value)
    
    
    def set_header(self, key, value):
#        self.response.headerlist.append((key, str(value)))
        self.response.headers[key] = str(value)
    
    
    def set_status(self, status):
        self.response.status = status
    
    