# -*- coding: utf-8 -*-
"""
Abstract Classes for Providers
------------------------------

Abstract base classes for implementation of protocol specific providers.

.. note::
    
    Attributes prefixed with ``_x_`` serve the purpose of unification
    of differences across providers.

.. autosummary::
    
    login_decorator
    BaseProvider
    AuthorisationProvider
    AuthenticationProvider

"""

from authomatic.exceptions import ConfigError, AuthenticationError, FetchError
import abc
import authomatic.core
import authomatic.settings as settings
import base64
import copy
import datetime
import hashlib
import httplib
import logging
import os
import random
import sys
import traceback
import urllib
import urlparse
import uuid

__all__ = ['BaseProvider', 'AuthorisationProvider', 'AuthenticationProvider', 'login_decorator']


def _write_error_traceback(exc_info, traceback):
    """
    Writes exception info and traceback to the response.
    
    :param tuple exc_info:
        Output of :finc:`sys.exc_info` function. 
        
    :param traceback:
        Output of :func:`traceback.format_exc` function.
    """
    
    html = """
    <html>
        <head>
            <title>ERROR: {error}</title>
        </head>
        <body style="font-family: sans-serif">
            <h4>The Authomatic library encountered an error!</h4>
            <h1>{error}</h1>
            <pre>{traceback}</pre>
        </body>
    </html>
    """
    
    authomatic.core.middleware.write(html.format(error=exc_info[1], traceback=traceback))


def login_decorator(func):
    """
    Decorate the :meth:`.BaseProvider.login` implementations with this decorator.
    
    Provides mechanism for error reporting and returning result
    which makes the :meth:`.BaseProvider.login` implementation cleaner.
    """
    
    def wrap(provider, *args, **kwargs):
        error = None
        result = authomatic.core.LoginResult(provider)
        
        try:
            func(provider, *args, **kwargs)
        except Exception as e:
            if settings.report_errors:
                error = e
                provider._log(logging.ERROR, 'Reported supressed exception: {}!'.format(repr(error)))
            else:
                if settings.debug:
                    _write_error_traceback(sys.exc_info(), traceback.format_exc())
                raise
        
        # If there is user or error the login procedure has finished
        if provider.user or error:
            # Add error to result
            result.error = error
            # Let middleware know that login procedure is over
            authomatic.core.middleware.block = False
            provider._log(logging.INFO, 'Procedure finished.')
        else:
            # Save session
            authomatic.core.middleware.save_session()
        
        # Return result       
        if result and provider.callback:
            provider.callback(result)
        return result
        
    return wrap


class BaseProvider(object):
    """
    Abstract base class for all providers.
    """
    
    PROVIDER_TYPE_ID = 0
    
    _repr_ignore = ('user',)
    
    __metaclass__ = abc.ABCMeta
    
    def __init__(self, provider_name, callback=None, js_callback=None,
                 prefix='authomatic', **kwargs):
        
        #: :class:`str` The provider name as specified in the :doc:`config`.
        self.name = provider_name
        
        #: :class:`callable` An optional callback called when the login procedure
        #: is finished with :class:`.core.LoginResult` passed as argument.
        self.callback = callback
        
        #: :class:`str` Name of an optional javascript callback.
        self.js_callback = js_callback
                
        #: :class:`.core.User`.
        self.user = None
    
    
    #===========================================================================
    # Abstract methods
    #===========================================================================
    
    @abc.abstractmethod
    def login(self):
        """
        Launches the *login procedure* to get **user's credentials** from **provider**.
        
        Should be decorated with :func:`.login_decorator`.
        The *login procedure* is considered finished when the :attr:`.user` attribute is
        not empty when the method runs out of it's flow or when there are errors.
        """
    
    #===========================================================================
    # Exposed methods
    #===========================================================================
    
    def to_dict(self):
        """
        Converts the provider instance to a :class:`dict`.
        
        :returns:
            :class:`dict`
        """
        
        return dict(name=self.name,
                    id=self.id,
                    type_id=self.type_id,
                    type=self.get_type(),
                    scope=self.scope if hasattr(self, 'scope') else None,
                    user=self.user.id if self.user else None)
    
    @classmethod
    def get_type(cls):
        """
        Returns the provider type.
        
        :returns:
            :class:`str` The full dotted path to base class e.g. :literal:`"authomatic.providers.oauth2.OAuth2"`. 
        """
        
        return cls.__module__ + '.' + cls.__bases__[0].__name__
    
    
    def update_user(self):
        """
        Updates and returns :attr:`.user`.
        
        :returns:
            :class:`.User`
        """
        
        return self.user
    
    
    #===========================================================================
    # Internal methods
    #===========================================================================
    
    @property
    def type_id(self):
        """
        A :class:`float` reprezenting the provider implementation id used for
        serialization of :class:`.Credentials` and to identify the type of provider in JavaScript.
        The part before period denotes the type of the provider, the part after period denotes the class id
        e.g. ``oauth2.Facebook.type_id = 2.5``, ``oauth1.Twitter.type_id = 1.5``.
        """
        
        # FIXME: type 1.1 and 1.10 are the same! It needs to be string.
        
        cls = self.__class__
        mod = sys.modules.get(cls.__module__)
        return self.PROVIDER_TYPE_ID + float(mod.PROVIDER_ID_MAP.index(cls)) / 1000
    
    
    def _kwarg(self, kwargs, kwname, default=None):
        """
        Resolves keyword arguments from constructor or :doc:`config`.
        
        .. note::
        
            The keyword arguments take this order of precedence:
            
            1. Arguments passed to constructor through the :func:`authomatic.login`.
            2. Provider specific arguments from :doc:`config`.
            3. Arguments from :doc:`config` set in the ``__defaults__`` key.
            2. The value from :data:`default` argument.
        
        :param dict kwargs:
            Keyword arguments dictionary.
        :param str kwname:
            Name of the desired keyword argument.
        """
        
        return kwargs.get(kwname) or \
               settings.config.get(self.name, {}).get(kwname) or \
               settings.config.get('__defaults__', {}).get(kwname) or \
               default
    
    
    def _session_key(self, key):
        """
        Generates session key string.
        
        :param str key:
            e.g. ``"authomatic:facebook:key"``
        """
        
        return '{}:{}:{}'.format(settings.prefix, self.name, key)
    
    
    def _session_set(self, key, value):
        """Saves a value to session."""
        
        authomatic.core.middleware.session[self._session_key(key)] = value
    
    
    def _session_get(self, key):
        """Retrieves a value from session."""
        
        return authomatic.core.middleware.session.get(self._session_key(key))
    
    
    @staticmethod
    def csrf_generator():
        """
        Generates CSRF token.
        
        Inspired by this article: http://blog.ptsecurity.com/2012/10/random-number-security-in-python.html
                
        :returns:
            :class:`str` Random unguessable string.
        """
        
        # Create hash from random string plus salt.
        hashed = hashlib.md5(str(uuid.uuid4()) + str(settings.secret)).hexdigest()
        
        # Each time return random portion of the hash.
        span = 5
        shift = random.randint(0, span)     
        return hashed[shift:shift - span - 1]
    
    
    @classmethod
    def _log(cls, level, msg):
        """
        Logs a message with preformated prefix.
        
        :param int level:
            Logging level as specified in the
            `login module <http://docs.python.org/2/library/logging.html>`_ of
            Python standard library.
        
        :param str msg:
            The actual message.
        """
        
        authomatic.core._logger.log(level, ': '.join((settings.prefix, cls.__name__, msg)))
        
    
    @classmethod
    def _fetch(cls, url, method='GET', params=None, headers=None, max_redirects=5, content_parser=None):
        """
        Fetches a URL.
        
        :param str url:
            The URL to fetch.
            
        :param str method:
            HTTP method of the request.
            
        :param dict params:
            Dictionary of request parameters.
            
        :param dict headers:
            HTTP headers of the request.
            
        :param int max_redirects:
            Number of maximum HTTP redirects to follow.
            
        :param function content_parser:
            A callable to be used to parse the :attr:`.Response.data` from :attr:`.Response.content`.
        """
        
        params = params or {}
        headers = headers or {}
        
        # Prepare URL elements
        scheme, host, path, query, fragment = urlparse.urlsplit(url)
        query = urllib.urlencode(params)
        request_path = urlparse.urlunsplit((None, None, path, query, None))
        
        # Apply headers from settings.
        headers.update(settings.fetch_headers)
        
        if method in ('POST', 'PUT', 'PATCH'):
            headers.update({'Content-Type': 'application/x-www-form-urlencoded'})
        
        cls._log(logging.DEBUG, u' \u251C\u2500 url: {}'.format(url))
        cls._log(logging.DEBUG, u' \u251C\u2500 method: {}'.format(method))
        cls._log(logging.DEBUG, u' \u251C\u2500 params: {}'.format(params))
        cls._log(logging.DEBUG, u' \u2514\u2500 headers: {}'.format(headers))
        
        # Connect
        if scheme.lower() == 'https':
            connection = httplib.HTTPSConnection(host)
        else:
            connection = httplib.HTTPConnection(host)
            
        try:
            connection.request(method, request_path, query, headers)
        except Exception as e:
            raise FetchError('Could not connect!',
                             original_message=e.message,
                             url=request_path)
        
        response = connection.getresponse()
        location = response.getheader('Location')
        
        if response.status in (300, 301, 302, 303, 307) and location:
            if location == url:
                raise FetchError('Url redirects to itself!',
                                 url=location,
                                 status=response.status)
                
            elif max_redirects > 0:
                remaining_redirects = max_redirects - 1
                
                cls._log(logging.DEBUG, 'Redirecting to {}'.format(url))
                cls._log(logging.DEBUG, 'Remaining redirects: '.format(remaining_redirects))
                
                # Call this method again.
                response = cls._fetch(url=location,
                                      body=body,
                                      method=method,
                                      headers=headers,
                                      max_redirects=remaining_redirects)
                
            else:
                raise FetchError('Max redirects reached!',
                                 url=location,
                                 status=response.status)
        else:
            cls._log(logging.DEBUG, u'Got response:')
            cls._log(logging.DEBUG, u' \u251C\u2500 url: {}'.format(url))
            cls._log(logging.DEBUG, u' \u251C\u2500 status: {}'.format(response.status))
            cls._log(logging.DEBUG, u' \u2514\u2500 headers: {}'.format(response.getheaders()))
                
        return authomatic.core.Response(response, content_parser)
    
    
    def _update_or_create_user(self, data, credentials=None, content=None):
        """
        Updates or creates :attr:`.user`.
        
        :returns:
            :class:`.User`
        """
        
        if not self.user:
            self.user = authomatic.core.User(self, credentials=credentials)
        
        self.user.content = content
        self.user.data = data
        
        # Update.
        for key in self.user.__dict__.keys():
            # Exclude data.
            if key not in ('data', 'content'):
                # Extract every data item whose key matches the user property name,
                # but only if it has a value.
                value = data.get(key)
                if value:
                    setattr(self.user, key, value)
             
        # Handle different structure of data by different providers.
        self.user = self._x_user_parser(self.user, data)
        
        # If there is no user.name,
        if not self.user.name:
            if self.user.first_name and self.user.last_name:
                # Create it from first name and last name if available.
                self.user.name = ' '.join((self.user.first_name, self.user.last_name))
            else:
                # Or use one of these.
                self.user.name = self.user.username or self.user.nickname or self.user.first_name or self.user.last_name
        
        return self.user    
    
    
    @staticmethod
    def _x_user_parser(user, data):
        """
        Handles different structure of user info data by different providers.
        
        :param user:
            :class:`.User`
        :param dict data:
            User info data returned by provider.
        """
        
        return user


class AuthorisationProvider(BaseProvider):
    """
    Base provider for *authorisation protocols* i.e. protocols which allow a **provider**
    to authorize a **consumer** to access **protected resources** of a **user**.
    e.g. `OAuth 2.0 <http://oauth.net/2/>`_ or `OAuth 1.0a <http://oauth.net/core/1.0a/>`_.    
    """
        
    USER_AUTHORISATION_REQUEST_TYPE = 2
    ACCESS_TOKEN_REQUEST_TYPE = 3
    PROTECTED_RESOURCE_REQUEST_TYPE = 4
    REFRESH_TOKEN_REQUEST_TYPE = 5
    
    BEARER = 'Bearer'
    
    _x_term_dict = {}
    
    #: If ``True`` the provider doesn't support Cross-site HTTP requests.
    same_origin = True
    
    # Whether to use the HTTP Authorisation header.
    _x_use_authorisation_header = True
    
    def __init__(self, *args, **kwargs):
        """
        Accepts additional keyword arguments:
        
        :arg str consumer_key:
            The *key* assigned to our application (**consumer**) by the **provider**.
            
        :arg str consumer_secret:
            The *secret* assigned to our application (**consumer**) by the **provider**.
            
        :arg int id:
            A unique numeric ID used to serialize :class:`.Credentials`.
            
        :arg dict user_authorisation_params:
            A dictionary of additional request parameters for **user authorisation request**.
            
        :arg dict access_token_params:
            A dictionary of additional request parameters for **access_with_credentials token request**.
        """
        
        super(AuthorisationProvider, self).__init__(*args, **kwargs)
        
        self.consumer_key = self._kwarg(kwargs, 'consumer_key')
        self.consumer_secret = self._kwarg(kwargs, 'consumer_secret')
        
        self.user_authorisation_params = self._kwarg(kwargs, 'user_authorisation_params', {})
        self.access_token_headers = self._kwarg(kwargs, 'user_authorisation_headers', {})
        
        self.access_token_params = self._kwarg(kwargs, 'access_token_params', {})
        
        self.id = self._kwarg(kwargs, 'id')
        
        #: :class:`.Credentials` to access **user's protected resources**.
        self.credentials = authomatic.core.Credentials(provider=self)
    
    #===========================================================================
    # Abstract properties
    #===========================================================================
        
    @abc.abstractproperty
    def user_authorisation_url(self):
        """
        :class:`str` URL to which we redirect the **user** to grant our app i.e. the **consumer**
        an **authorisation** to access his **protected resources**.
        see http://tools.ietf.org/html/rfc6749#section-4.1.1 and
        http://oauth.net/core/1.0a/#auth_step2.
        """
    
    
    @abc.abstractproperty
    def access_token_url(self):
        """
        :class:`str` URL where we can get the *access token* to access **protected resources** of a **user**.
        see http://tools.ietf.org/html/rfc6749#section-4.1.3 and
        http://oauth.net/core/1.0a/#auth_step3.
        """
    
    
    @abc.abstractproperty
    def user_info_url(self):
        """        
        :class:`str` URL where we can get the **user** info.
        see http://tools.ietf.org/html/rfc6749#section-7 and
        http://oauth.net/core/1.0a/#anchor12.
        """
    
    
    #===========================================================================
    # Abstract methods
    #===========================================================================
    
    @abc.abstractmethod
    def to_tuple(self, credentials):
        """
        Must convert :data:`credentials` to a :class:`tuple` to be used by :meth:`.Credentials.serialize`.
        
        .. warning::
        
            |classmethod|
        
        :param credentials:
            :class:`.Credentials`
            
        :returns:
            :class:`tuple`
        """
    
    
    @abc.abstractmethod
    def reconstruct(self, deserialized_tuple, credentials, cfg):
        """
        Must convert the :data:`deserialized_tuple` back to :class:`.Credentials`.
        
        .. warning::
        
            |classmethod|
        
        :param tuple deserialized_tuple:
            A tuple whose first index is the :attr:`.id` and the rest
            are all the items of the :class:`tuple` created by :meth:`.to_tuple`.
        
        :param credentials:
            A :class:`.Credentials` instance.
            
        :param dict cfg:
            Provider configuration from :doc:`config`. 
        """
    
    
    @abc.abstractmethod
    def create_request_elements(self, request_type, credentials, url, method='GET', params=None, headers=None):
        """
        Must return :class:`.RequestElements`.
        
        .. warning::
        
            |classmethod|
        
        :param int request_type:
            Type of the request specified by one of the classe's constants.
            
        :param credentials:
            :class:`.Credentials` of the **user** whose
            **protected resource** we want to access.
            
        :param str url:
            URL of the request.
            
        :param str method:
            HTTP method of the request.
            
        :param dict params:
            Dictionary of request parameters.
            
        :param dict headers:
            Dictionary of request headers.
        
        :returns:
            :class:`.RequestElements`
        """
    
    
    #===========================================================================
    # Exposed methods
    #===========================================================================
    
    @classmethod
    def access_with_credentials(cls, credentials, url, params=None, method='GET',
                                headers=None, max_redirects=5, content_parser=None):
        """
        Fetches the **protected resource** of the **user** to whom belong
        the supplied :data:`.credentials`.
        
        :param credentials:
        The **user's** :class:`.Credentials` (serialized or normal).
            
        :param str url:
            The URL of the **protected resource**.
            
        :param str method:
            HTTP method of the request.
            
        :param dict headers:
            HTTP headers of the request.
            
        :param int max_redirects:
            Maximum number of HTTP redirects to follow.
            
        :param function content_parser:
            A function to be used to parse the :attr:`.Response.data` from :attr:`.Response.content`.
        
        :returns:
            :class:`.Response`
        """
        
        headers = headers or {}
        
        cls._log(logging.INFO, 'Accessing protected resource {}.'.format(url))
        
        request_elements = cls.create_request_elements(request_type=cls.PROTECTED_RESOURCE_REQUEST_TYPE,
                                                        credentials=credentials,
                                                        url=url,
                                                        params=params,
                                                        method=method)
        
        response = cls._fetch(*request_elements,
                              max_redirects=max_redirects,
                              content_parser=content_parser)
        
        cls._log(logging.INFO, 'Got response. HTTP status = {}.'.format(response.status))
        return response
    
    
    def access(self, url, params=None, method='GET', headers={}, max_redirects=5, content_parser=None):
        """
        Fetches the **protected resource** of the logged in **user**.
        
        :param credentials:
            The **user's** :class:`.Credentials` (serialized or normal).
            
        :param str method:
            HTTP method of the request.
            
        :param dict headers:
            HTTP headers of the request.
            
        :param int max_redirects:
            Maximum number of HTTP redirects to follow.
            
        :param function content_parser:
            A function to be used to parse the :attr:`.Response.data` from :attr:`.Response.content`.
        
        :returns:
            :class:`.Response`
        """
        
        return self.access_with_credentials(credentials=self.credentials,
                                            url=url,
                                            params=params,
                                            method=method,
                                            headers=headers,
                                            max_redirects=max_redirects,
                                            content_parser=content_parser)


    def async_access(self, *args, **kwargs):
        """
        Same as :meth:`.access` but runs asynchronously in a separate thread.
        
        .. warning:: |async|
        
        :returns:
            :class:`.Future` instance representing the separate thread.
        """
        
        return authomatic.core.Future(self.access, *args, **kwargs)
    
    
    def update_user(self):
        """
        Updates the :attr:`.BaseProvider.user`.
        
        .. warning::
        
            Fetches the :attr:`.user_info_url`!
        
        :returns:
            :class:`.UserInfoResponse`
        """
        
        if self.user_info_url:
            return self._access_user_info()
    
    
    #===========================================================================
    # Internal methods
    #===========================================================================
    
    @classmethod
    def _authorisation_header(cls, credentials):
        """
        Creates authorisation headers if the provider supports it.
        See: http://en.wikipedia.org/wiki/Basic_access_authentication.
        
        :param credentials:
            :class:`.Credentials`
        
        :returns:
            Headers as :class:`dict`.
        """
        
        if cls._x_use_authorisation_header:
            res = ':'.join((credentials.consumer_key, credentials.consumer_secret))
            res = base64.b64encode(res)
            return {'Authorization': 'Basic {}'.format(res)}
        else:
            return {}
    
    
    def _check_consumer(self):
        """
        Validates the :attr:`.consumer`.
        """
        
        if not self.consumer.key:
            raise ConfigError('Consumer key not specified for provider {}!'.format(self.name))
        
        if not self.consumer.secret:
            raise ConfigError('Consumer secret not specified for provider {}!'.format(self.name))
    
    
    @staticmethod
    def _split_url(url):
        "Splits given url to url base and params converted to list of tuples"
        
        split = urlparse.urlsplit(url)
        base = urlparse.urlunsplit((split.scheme, split.netloc, split.path, 0, 0))
        params = urlparse.parse_qsl(split.query, True)
        
        return base, params
    
    
    @staticmethod
    def _x_credentials_parser(credentials, data):
        """
        Override this to handle differences in naming conventions across providers.
        
        :param credentials:
            :class:`.Credentials`
            
        :param dict data:
            Response data dictionary.
            
        :returns:
            :class:`.Credentials`
        """
        return credentials
    
    
    def _access_user_info(self):
        """
        Accesses the :attr:`.user_info_url`.
        
        :returns:
            :class:`.UserInfoResponse`
        """
        
        url = self.user_info_url.format(**self.user.__dict__)
        
        logging.info('USER INFO URL: {}'.format(url))
        
        response = self.access_with_credentials(self.credentials, url)
        
        # Create user.
        self.user = self._update_or_create_user(response.data, content=response.content)
        
        # Return UserInfoResponse.
        return authomatic.core.UserInfoResponse(self.user, response.httplib_response)
    

class AuthenticationProvider(BaseProvider):
    """
    Base provider for *authentication protocols* i.e. protocols which allow a **provider** to
    authenticate a *claimed identity* of a **user**. e.g. `OpenID <http://openid.net/>`_.
    """
    
    #: Indicates whether the **provider** supports access_with_credentials to
    #: **user's** protected resources.
    # TODO: Useless
    has_protected_resources = False
    
    def __init__(self, *args, **kwargs):   
        super(AuthenticationProvider, self).__init__(*args, **kwargs)
        
        # Allow for custom name for the "id" querystring parameter.
        self.identifier_param = kwargs.get('identifier_param', 'id')
        
        # Get the identifier from request params.
        self.identifier = authomatic.core.middleware.params.get(self.identifier_param)
        

PROVIDER_ID_MAP = [BaseProvider, AuthorisationProvider, AuthenticationProvider]
        












