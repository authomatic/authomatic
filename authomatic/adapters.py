# -*- coding: utf-8 -*-
"""
Adapters
--------

.. contents::
   :backlinks: none

The :func:`authomatic.login` function needs access to functionality like
getting the **URL** of the handler where it is being called, getting the
**request params** and **cookies** and **writing the body**, **headers**
and **status** to the response.

Since implementation of these features varies across Python web frameworks,
the Authomatic library uses **adapters** to unify these differences into a
single interface.

Available Adapters
^^^^^^^^^^^^^^^^^^

If you are missing an adapter for the framework of your choice, please
open an `enhancement issue <https://github.com/authomatic/authomatic/issues>`_
or consider a contribution to this module by
:ref:`implementing <implement_adapters>` one by yourself.
Its very easy and shouldn't take you more than a few minutes.

.. autoclass:: DjangoAdapter
    :members:

.. autoclass:: Webapp2Adapter
    :members:

.. autoclass:: WebObAdapter
    :members:

.. autoclass:: WerkzeugAdapter
    :members:

.. _implement_adapters:

Implementing an Adapter
^^^^^^^^^^^^^^^^^^^^^^^

Implementing an adapter for a Python web framework is pretty easy.

Do it by subclassing the :class:`.BaseAdapter` abstract class.
There are only **six** members that you need to implement.

Moreover if your framework is based on the |webob|_ or |werkzeug|_ package
you can subclass the :class:`.WebObAdapter` or :class:`.WerkzeugAdapter`
respectively.

.. autoclass:: BaseAdapter
    :members:

"""

import abc


class BaseAdapter():
    """
    Base class for platform adapters.

    Defines common interface for WSGI framework specific functionality.

    """

    __metaclass__ = abc.ABCMeta

    @property
    @abc.abstractmethod
    def params(self):
        """
        Must return a :class:`dict` of all request parameters of any HTTP
        method.

        :returns:
            :class:`dict`

        """

    @property
    @abc.abstractmethod
    def url(self):
        """
        Must return the url of the actual request including path but without
        query and fragment.

        :returns:
            :class:`str`

        """

    @property
    @abc.abstractmethod
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

        :param str status:
            The HTTP response status.

        """


class DjangoAdapter(BaseAdapter):
    """
    Adapter for the |django|_ framework.
    """

    def __init__(self, request, response):
        """
        :param request:
            An instance of the :class:`django.http.HttpRequest` class.

        :param response:
            An instance of the :class:`django.http.HttpResponse` class.
        """
        self.request = request
        self.response = response

    @property
    def params(self):
        params = {}
        params.update(self.request.GET.dict())
        params.update(self.request.POST.dict())
        return params

    @property
    def url(self):
        return self.request.build_absolute_uri(self.request.path)

    @property
    def cookies(self):
        return dict(self.request.COOKIES)

    def write(self, value):
        self.response.write(value)

    def set_header(self, key, value):
        self.response[key] = value

    def set_status(self, status):
        status_code = status.split(' ', 1)[0]
        self.response.status_code = int(status_code)


class WebObAdapter(BaseAdapter):
    """
    Adapter for the |webob|_ package.
    """

    def __init__(self, request, response):
        """
        :param request:
            A |webob|_ :class:`Request` instance.

        :param response:
            A |webob|_ :class:`Response` instance.
        """
        self.request = request
        self.response = response

    # =========================================================================
    # Request
    # =========================================================================

    @property
    def url(self):
        return self.request.path_url

    @property
    def params(self):
        return dict(self.request.params)

    @property
    def cookies(self):
        return dict(self.request.cookies)

    # =========================================================================
    # Response
    # =========================================================================

    def write(self, value):
        self.response.write(value)

    def set_header(self, key, value):
        self.response.headers[key] = str(value)

    def set_status(self, status):
        self.response.status = status


class Webapp2Adapter(WebObAdapter):
    """
    Adapter for the |webapp2|_ framework.

    Inherits from the :class:`.WebObAdapter`.

    """

    def __init__(self, handler):
        """
        :param handler:
            A :class:`webapp2.RequestHandler` instance.
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
    def cookies(self):
        return self.request.cookies

    def __init__(self, request, response):
        """
        :param request:
            Instance of the :class:`werkzeug.wrappers.Request` class.

        :param response:
            Instance of the :class:`werkzeug.wrappers.Response` class.
        """

        self.request = request
        self.response = response

    def write(self, value):
        self.response.data = self.response.data.decode('utf-8') + value

    def set_header(self, key, value):
        self.response.headers[key] = value

    def set_status(self, status):
        self.response.status = status
