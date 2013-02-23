"""
Abstract Classes for Providers
------------------------------

Abstract base classes for implementation of protocol specific providers.

.. autosummary::
    
    login_decorator
    BaseProvider
    AuthorisationProvider
    AuthenticationProvider

"""

from authomatic.exceptions import ConfigError, AuthenticationError, FetchError
import abc
import authomatic.core
import datetime
import hashlib
import httplib
import logging
import os
import random
import urlparse
import uuid
import authomatic.settings as settings

__all__ = ['BaseProvider', 'AuthorisationProvider', 'AuthenticationProvider', 'login_decorator']

def login_decorator(func):
    """
    Decorator to be used by the :meth:`.BaseProvider.login`.
    
    Provides mechanism for error reporting and returning result
    which makes the :meth:`.BaseProvider.login` implementation cleaner.
    """
    
    def wrap(provider, *args, **kwargs):
        error = None
        
        if settings.report_errors:
            # Catch and report errors.
            try:
                func(provider, *args, **kwargs)
            except Exception as e:
                error = e
                provider._log(logging.ERROR, 'Reported supressed exception: {}!'.format(repr(error)))
        else:
            # Don't handle errors.
            func(provider, *args, **kwargs)
        
        # If there is user or error the login procedure has finished
        if provider.user or error:
            result = authomatic.core.LoginResult(provider, error)
            if provider.callback:
                provider.callback(result)
                provider._log(logging.INFO, 'Procedure finished.')
                authomatic.core.middleware.pending = False
            return result
    
    return wrap


class BaseProvider(object):
    """
    Abstract base class for all providers.
    """
    
    
    _repr_ignore = ('user',)
    
    __metaclass__ = abc.ABCMeta
    
    def __init__(self, provider_name, callback=None,
                 prefix='authomatic', **kwargs):
        
        #: :class:`str` The provider name as specified in the :doc:`config`.
        self.name = provider_name
        
        #: :class:`callable` An optional callback called when the login procedure
        #: is finished with :class:`.core.LoginResult` passed as argument.
        self.callback = callback
                
        #: :class:`.core.User`.
        self.user = None        
        
        self._user_info_request = None
        
        # setup _logger
#        self._logger = logging.getLogger(__name__)
#        self._logger.setLevel(settings.logging_level)
#        if settings.logging_level in (None, False):
#            self._logger.disabled = False
    
    
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
            :class:`.core.User`
        """
        
        return self.user
    
    
    #===========================================================================
    # Internal methods
    #===========================================================================
    
    
    def _kwarg(self, kwargs, kwname, default=None):
        """
        Resolves keyword arguments from constructor or :doc:`config`.
        
        .. note::
        
            Arguments from :doc:`config` take precedence over those from constructor.
        
        :param dict kwargs:
            Keyword arguments dictionary.
        :param str kwname:
            Name of the desired keyword argument.
        """
        
        return settings.config.get(self.name, {}).get(kwname) or \
               settings.config.get('__defaults__', {}).get(kwname) or \
               kwargs.get(kwname) or default
    
    
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
    
    
    @classmethod
    def csrf_generator(cls):
        """
        Generates CSRF token.
        
        Inspired by this article http://blog.ptsecurity.com/2012/10/random-number-security-in-python.html
                
        :returns:
            :class:`str` Random unguessable string.
        """
        
        # TODO: Move to utils.
        
        return hashlib.md5(str(uuid.uuid4())).hexdigest()
    
    
    @classmethod
    def _log(cls, level, msg):
        """
        Logs a message.
        
        :param int level:
            Logging level as specified in the
            `login module <http://docs.python.org/2/library/logging.html>`_ of
            Python standard library.
        :param str msg:
            The actual message.
        """
        
        authomatic.core._logger.log(level, ': '.join((settings.prefix, cls.__name__, msg)))
        
    
    @classmethod
    def _fetch(cls, url, body='', method='GET', headers={}, max_redirects=5, content_parser=None):
        
        cls._log(logging.DEBUG, 'Fetching url {}'.format(url))
        
        # Prepare URL elements
        scheme, host, path, query, fragment = urlparse.urlsplit(url)
        request_path = urlparse.urlunsplit((None, None, path, query, None))
        
        # Connect
        connection = httplib.HTTPSConnection(host)
        try:
            connection.request(method, request_path, body, headers)
        except Exception as e:
            raise FetchError('Could not connect!',
                             original_message=e.message,
                             url=request_path)
        
        response = connection.getresponse()
        
        location = response.getheader('Location')
        
        if response.status in (300, 301, 302, 303, 307) and location:
            if location == url:
                raise FetchError('Url redirects to itself!',
                                 url=location)
                
            elif max_redirects > 0:
                remaining_redirects = max_redirects - 1
                
                cls._log(logging.DEBUG, 'Redirecting to {}'.format(url))
                cls._log(logging.DEBUG, 'Remaining redirect attempts: '.format(remaining_redirects))
                
                # Call this method again.
                response = cls._fetch(url=location,
                                      body=body,
                                      method=method,
                                      headers=headers,
                                      max_redirects=remaining_redirects)
                
            else:
                raise FetchError('Max redirects reached!',
                                 url=location)
        else:
            cls._log(logging.DEBUG, 'Got response from {}'.format(url))
                
        return authomatic.core.Response(response, content_parser)
    
    
    def _update_or_create_user(self, data, credentials=None):
        """
        Updates or creates :attr:`.user`.
        
        :returns:
            :class:`.core.User`
        """
        
        if not self.user:
            self.user = authomatic.core.User(self, credentials=credentials)
        
        self.user.raw_user_info = data
        
        # Update.
        for key in self.user.__dict__.keys():
            # Exclude raw_user_info.
            if key is not 'raw_user_info':
                # Extract every data item whose key matches the user property name,
                # but only if it has a value.
                value = data.get(key)
                if value:
                    setattr(self.user, key, value)
                    
        # Handle different structure of data by different providers.
        self.user = self._user_parser(self.user, data)
        
        return self.user    
    
    
    @staticmethod
    def _user_parser(user, data):
        """
        Handles different structure of user info data by different providers.
        
        :param core.Users user:
            :class:`.core.Users`
        :param dict data:
            User info data returned by provider.
        """
        
        return user


class AuthorisationProvider(BaseProvider):
    """
    Base provider for *authorisation protocols* i.e. protocols which allow a **consumer**
    to be authorized by a **provider** to access_with_credentials **protected resources** of a **user**.
    e.g. `OAuth 2.0 <http://oauth.net/2/>`_ or `OAuth 1.0a <http://oauth.net/core/1.0a/>`_.    
    """
        
    USER_AUTHORISATION_REQUEST_TYPE = 2
    ACCESS_TOKEN_REQUEST_TYPE = 3
    PROTECTED_RESOURCE_REQUEST_TYPE = 4
    REFRESH_TOKEN_REQUEST_TYPE = 5
    
    def __init__(self, *args, **kwargs):
        """
        Accepts additional keyword arguments:
        
        :arg str consumer_key:
            The *key* assigned to our application (**consumer**) by the **provider**.
        :arg str consumer_secret:
            The *secret* assigned to our application (**consumer**) by the **provider**.
        :arg short_name:
            A unique short name used to serialize :class:`.Credentials`.
        :arg dict user_authorisation_params:
            A dictionary of additional request parameters for **user authorisation request**.
        :arg dict access_token_params:
            A dictionary of additional request parameters for **access_with_credentials token request**.
        """
        
        super(AuthorisationProvider, self).__init__(*args, **kwargs)
        
        self.consumer_key = self._kwarg(kwargs, 'consumer_key')
        self.consumer_secret = self._kwarg(kwargs, 'consumer_secret')
        self.short_name = self._kwarg(kwargs, 'short_name')
        
        self.user_authorisation_params = self._kwarg(kwargs, 'user_authorisation_params', {})
        self.access_token_params = self._kwarg(kwargs, 'access_token_params', {})
        
        #: :class:`core.Credentials` to access_with_credentials **user's protected resources**.
        self.credentials = authomatic.core.Credentials(provider=self)
    
    
    #===========================================================================
    # Abstract properties
    #===========================================================================
        
    @abc.abstractproperty
    def user_authorisation_url(self):
        """
        :class:`str` URL to which we redirect the **user** to grant our app i.e. the **consumer**
        an **authorisation** to access_with_credentials his **protected resources**.
        see http://tools.ietf.org/html/rfc6749#section-4.1.1 and
        http://oauth.net/core/1.0a/#auth_step2.
        """
    
    @abc.abstractproperty
    def access_token_url(self):
        """
        :class:`str` URL where we can get the *access_with_credentials token* to access_with_credentials **protected resources** of a **user**.
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
        Must convert :data:`credentials` to a :class:`tuple` to be used by :meth:`.core.Credentials.serialize`.
        
        .. warning::
        
            |classmethod|
        
        :param core.Credentials credentials:
            :class:`.core.Credentials`
        :returns:
            :class:`tuple`
        """
    
    
    @abc.abstractmethod
    def reconstruct(self, deserialized_tuple, cfg):
        """
        Must convert the :data:`deserialized_tuple` back to :class:`.core.Credentials`.
        
        .. warning::
        
            |classmethod|
        
        :param tuple deserialized_tuple:
            A tuple which first index is the :attr:`.short_name` and the rest
            are all the items of the :class:`tuple` created by :meth:`.to_tuple`.
        :param dict cfg:
            :doc:`config`
        """
    
    
    @classmethod
    def access_with_credentials(cls, credentials, url, method='GET', headers={}, max_redirects=5, content_parser=None):
        
        cls._log(logging.INFO, 'Accessing protected resource {}.'.format(url))
        
        request_elements = cls._create_request_elements(request_type=cls.PROTECTED_RESOURCE_REQUEST_TYPE,
                                                        credentials=credentials,
                                                        url=url,
                                                        method=method,
                                                        csrf=cls.csrf_generator())
        
        response = cls._fetch(*request_elements,
                              headers=headers,
                              max_redirects=max_redirects,
                              content_parser=content_parser)
        
        cls._log(logging.INFO, 'Got response. HTTP status = {}.'.format(response.status))
        return response
    
    
    def access(self, url, method='GET', headers={}, max_redirects=5, content_parser=None):
        return self.access_with_credentials(self.credentials, url, method,
                                            headers, max_redirects, content_parser)
    
    
    @abc.abstractmethod
    def _create_request_elements(self, request_type, credentials, url, method='GET'):
        """
        Must create a :class:`tuple` with this structure ``(url, body, method)``,
        where *url* must be the request url without query parameters and fragment,
        *body* is the request body and *method* is the :data:`method`.
        
        .. warning::
        
            |classmethod|
        
        :param request_type:
            Type of the request specified by one of the classe's constants.
        :param core.Credentials credentials:
            :class:`Credentials <.core.Credentials>` of the **user** whose
            **protected resource** we want to access_with_credentials.
        :param str url:
            URL of the request.
        :param method:
            HTTP method of the request.
        
        :returns:
            A (url, body, method) tuple.
        """
    
    
    #===========================================================================
    # Exposed methods
    #===========================================================================
    
    
    def update_user(self):
        """
        Updates the :attr:`user <.BaseProvider.user>`.
        
        .. warning::
        
            Makes a request to :attr:`.user_info_url`!
        
        :returns:
            :class:`.core.User`
        """
        
        return self.access_user_info().user
    
    
    def access_user_info(self):
        response = self.access_with_credentials(self.credentials, self.user_info_url)
        
        # Create user.
        self.user = self._update_or_create_user(response.data)
        
        # Return UserInfoResponse.
        return authomatic.core.UserInfoResponse(self.user, response.httplib_response)
    
    
    #===========================================================================
    # Internal methods
    #===========================================================================
    
    
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
    def _credentials_parser(credentials, data):
        """
        Override this to handle differences in naming conventions of providers.
        
        :param core.Credentials credentials:
            :class:`.core.Credentials`
        :param dict data:
            Response data dictionary
        :returns:
            :class:`.core.Credentials`
        """
        return credentials
    

class AuthenticationProvider(BaseProvider):
    """
    Base provider for *authentication protocols* i.e. protocols which allow a **provider** to
    authenticate a *claimed identity* of a **user**. e.g. `OpenID <http://openid.net/>`_.
    """
    
    #: Indicates whether the **provider** supports access_with_credentials to
    #: **user's** protected resources.
    has_protected_resources = False
    
    def __init__(self, *args, **kwargs):   
        super(AuthenticationProvider, self).__init__(*args, **kwargs)
        
        self.identifier_param = kwargs.get('identifier_param', 'id')
        
        self.identifier = authomatic.core.middleware.params.get(self.identifier_param)
        
        
        












