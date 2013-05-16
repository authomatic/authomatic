# -*- coding: utf-8 -*-
"""
Adapters
--------

.. contents::
   :backlinks: none

The :func:`authomatic.login` function needs access to functionality like
getting the url of the handler where it is called, getting the request params, headers and cookies and
writing the body, headers and status to the response.

Since implementation of these features varies across Python web frameworks,
the Authomatic library uses **adapters** to unify these differences into a single interface.

Available Adapters
^^^^^^^^^^^^^^^^^^

Currently there is only the :class:`.Webapp2Adapter` available.

.. autoclass:: Webapp2Adapter
    :members:

Implementing an Adapter
^^^^^^^^^^^^^^^^^^^^^^^

Implementing an adapter for a Python web framework is pretty easy.

You do it by subclassing the :class:`.BaseAdapter` abstract class.
There are only **seven** members that you need to implement.

Moreover if your framework is based on the |webob|_ library
you can subclass the :class:`.WebObBaseAdapter` and you only need to
override the constructor.

.. autoclass:: BaseAdapter
    :members:
    
.. autoclass:: WebObBaseAdapter
    :members:
"""

import abc


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
        To set the status in JSON endpoint.
        """


class WebObBaseAdapter(BaseAdapter):
    """
    Abstract base class for adapters for |webob|_ based frameworks.
    
    If you use this base class you only need to set the
    :attr:`.BaseAdapter.request` to the |webob|_ :class:`Request` and
    :attr:`.BaseAdapter.response` to the |webob|_ :class:`Response`
    in the constructor.
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
        self.response.headers[key] = str(value)
    
    
    def set_status(self, status):
        self.response.status = status
    

class Webapp2Adapter(WebObBaseAdapter):
    """
    Adapter for the |webapp2|_ framework.
    """
    
    request = None
    response = None
    
    def __init__(self, handler):
        """
        :param handler:
        
            A |webapp2|_ :class:`RequestHandler` instance.
        """
        
        self.request = handler.request
        self.response = handler.response


