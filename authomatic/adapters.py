# -*- coding: utf-8 -*-
"""
Adapters
--------

.. contents::
   :backlinks: none

The :func:`authomatic.login` function needs access to functionality like
getting the **URL** of the handler where it is being called, getting the **request params**, **headers** and **cookies** and
**writing the body**, **headers** and **status** to the response.

Since implementation of these features varies across Python web frameworks,
the Authomatic library uses **adapters** to unify these differences into a single interface.

Available Adapters
^^^^^^^^^^^^^^^^^^

If you are missing an adapter for the framework of your choice, which is very likely, since
currently there are only the :class:`.Webapp2Adapter` and :class:`.WerkzeugAdapter` available,
please consider a contribution to this module by :ref:`implementing <implement_adapters>` one.
Its very easy and shouldn't take you more than a few minutes.

.. autoclass:: Webapp2Adapter
    :members:

.. autoclass:: WerkzeugAdapter
    :members:

.. _implement_adapters:

Implementing an Adapter
^^^^^^^^^^^^^^^^^^^^^^^

Implementing an adapter for a Python web framework is pretty easy.

Do it by subclassing the :class:`.BaseAdapter` abstract class.
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


    @abc.abstractproperty
    def params(self):
        """
        Must return a :class:`dict` of all request parameters of any HTTP method.

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


    @abc.abstractproperty
    def headers(self):
        """
        Must return the request headers as a :class:`dict`.

        :returns:
            :class:`dict`
        """


    @abc.abstractproperty
    def cookies(self):
        """
        Must return cookies as a :class:`dict`.

        :returns:
            :class:`dict`
        """


    @abc.abstractmethod
    def write(self, value):
        """
        Must write specified value to response.

        :param str value:
            String to be written to response.
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
    def set_status(self, status):
        """
        Must set the response status e.g. ``'302 Found'``.

        :param str key:
            The HTTP response status.
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


class WerkzeugAdapter(BaseAdapter):
    """
    Adapter for |flask|_ and other |werkzeug|_ based frameworks.
    
    Thanks to `Mark Steve Samson <http://marksteve.com>`_.
    """

    @property
    def params(self):
        return self.request.args

    @property
    def url(self):
        return self.request.base_url

    @property
    def headers(self):
        return self.request.headers

    @property
    def cookies(self):
        return self.request.cookies

    def __init__(self, request, response):
        """
        :param request:
            Instance of the |werkzeug|_ `Request <http://werkzeug.pocoo.org/docs/wrappers/#werkzeug.wrappers.Request>`_ class.
            
        :param response:
            Instance of the |werkzeug|_ `Response <http://werkzeug.pocoo.org/docs/wrappers/#werkzeug.wrappers.Response>`_ class.
        """
        
        self.request = request
        self.response = response

    def write(self, value):
        self.response.data += value

    def set_header(self, key, value):
        self.response.headers[key] = value

    def set_status(self, status):
        self.response.status = status
