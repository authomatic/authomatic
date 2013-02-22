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

__all__ = ['BaseProvider', 'AuthorisationProvider', 'AuthenticationProvider', 'login_decorator']

def login_decorator(func):
    """
    Decorator to be used by the :meth:`.BaseProvider.login`.
    
    Provides mechanism for error reporting and returning result
    which makes the :meth:`.BaseProvider.login` implementation cleaner.
    """
    
    def wrap(provider, *args, **kwargs):
        error = None
        
        if provider.report_errors:
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
            return result
    
    return wrap


class BaseProvider(object):
    """
    Abstract base class for all providers.
    """
    
    
    _repr_ignore = ('user',)
    
    __metaclass__ = abc.ABCMeta
    
    def __init__(self, provider_name, callback=None,
                 report_errors=True, logging_level=logging.INFO,
                 prefix='authomatic', **kwargs):
        
        #: :class:`str` The provider name as specified in the :doc:`config`.
        self.name = provider_name
        
        #: :class:`callable` An optional callback called when the login procedure
        #: is finished with :class:`.core.LoginResult` passed as argument.
        self.callback = callback
        
        #: :class:`bool` If :literal:`True` exceptions which occur inside the :meth:`.login`
        #: will be caught and reported in the :attr:`.core.LoginResult.error`.
        self.report_errors = report_errors
        
        #: :class:`int` The logging level treshold as specified in the standard Python
        #: `logging library <http://docs.python.org/2/library/logging.html>`_.
        #: If :literal:`None` or :literal:`False` there will be no logs. Default is ``logging.INFO``.
        self.logging_level = logging_level
        
        #: :class:`str` Prefix used by storing values to session.
        self.prefix = prefix
        
        #: :class:`.core.User`.
        self.user = None
        
        
        self._user_info_request = None
        
        #TODO: Make _logger private
        # setup _logger
        self._logger = logging.getLogger(__name__)
        self._logger.setLevel(logging_level)
        if logging_level in (None, False):
            self._logger.disabled = False
    
    
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
    def new_fetch(cls, credentials, url, method='GET', headers={}, content_parser=None):
        
        request_elements = cls._create_request_elements(request_type=cls.PROTECTED_RESOURCE_REQUEST_TYPE,
                                                        credentials=credentials,
                                                        url=url,
                                                        method=method,
                                                        csrf=cls.csrf_generator())
        
        return cls._new_fetch(*request_elements,
                              headers=headers,
                              content_parser=content_parser)
    
    
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
        
        return authomatic.core.mw.config.get(self.name, {}).get(kwname) or \
               authomatic.core.mw.config.get('__defaults__', {}).get(kwname) or \
               kwargs.get(kwname) or default
    
    
    def _session_key(self, key):
        """
        Generates session key string.
        
        :param str key:
            e.g. ``"authomatic:facebook:key"``
        """
        
        return '{}:{}:{}'.format(self.prefix, self.name, key)
    
    
    def _session_set(self, key, value):
        """Saves a value to session."""
        
        authomatic.core.mw.session[self._session_key(key)] = value
    
    
    def _session_get(self, key):
        """Retrieves a value from session."""
        return authomatic.core.mw.session.get(self._session_key(key))
    
    
    @classmethod
    def csrf_generator(cls):
        """
        Generates CSRF token.
        
        Inspired by this article http://blog.ptsecurity.com/2012/10/random-number-security-in-python.html
                
        :returns:
            :class:`str` Random unguessable string.
        """
        
        
        
        return hashlib.md5(str(uuid.uuid4())).hexdigest()
    
    
    def _log(self, level, msg):
        """
        Logs a message.
        
        :param int level:
            Logging level as specified in the
            `login module <http://docs.python.org/2/library/logging.html>`_ of
            Python standard library.
        :param str msg:
            The actual message.
        """
        
        # Prefix each message with base
        base = '{}: {}: '.format(self.prefix, self.__class__.__name__)
        
        self._logger.log(level, base + msg)
        
    
    @classmethod
    def _new_fetch(cls, url, body='', method='GET', headers={}, max_redirects=4, content_parser=None):
        
        logging.info('Fetching url = {}'.format(url))
        logging.info('remaining redirects = {}'.format(max_redirects))
        
        # Prepare URL elements
        scheme, host, path, query, fragment = urlparse.urlsplit(url)
        request_path = urlparse.urlunsplit((None, None, path, query, None))
        
        # Connect
        connection = httplib.HTTPSConnection(host)
        try:
            connection.request(method, request_path, body, headers)
        except Exception as e:
            raise FetchError('Could not connect! Error: {}'.format(e.message))
        
        response = connection.getresponse()
        
        location = response.getheader('Location')
        
        if response.status in (300, 301, 302, 303, 307) and location:
            if location == url:
                raise FetchError('Loop redirect to = {}'.format(location))
            elif max_redirects > 0:
                logging.info('Redirecting to = {}'.format(location))
                response = cls.new_fetch(location, body, method, headers, max_redirects=max_redirects - 1)
            else:
                raise FetchError('Max redirects reached!')
        else:
            logging.info('Got response from url = {}'.format(url))
        
        
        return authomatic.core.Response(status_code=response.status,
                                        headers=dict(response.getheaders()),
                                        content=response.read(),
                                        content_parser=content_parser)
    
    
    def _update_or_create_user(self, data, credentials=None):
        """
        Updates or creates :attr:`.user`.
        
        :returns:
            :class:`.core.User`
        """
        
        if not self.user:
            # Create.
            self._log(logging.INFO, 'Creating user.')
            self.user = authomatic.core.User(self, credentials=credentials)
        else:
            self._log(logging.INFO, 'Updating user.')
        
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
    to be authorized by a **provider** to access **protected resources** of a **user**.
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
            A dictionary of additional request parameters for **access token request**.
        """
        
        super(AuthorisationProvider, self).__init__(*args, **kwargs)
        
        self.consumer_key = self._kwarg(kwargs, 'consumer_key')
        self.consumer_secret = self._kwarg(kwargs, 'consumer_secret')
        self.short_name = self._kwarg(kwargs, 'short_name')
        
        self.user_authorisation_params = self._kwarg(kwargs, 'user_authorisation_params', {})
        self.access_token_params = self._kwarg(kwargs, 'access_token_params', {})
        
        #: :class:`core.Credentials` to access **user's protected resources**.
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
            **protected resource** we want to access.
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
        
        return self.new_fetch_user_info().user
    
    
    def new_fetch_user_info(self):
        response = self.new_fetch(self.credentials, self.user_info_url)
        
        # Create user.
        self.user = self._update_or_create_user(response.data)
        
        # Return UserInfoResponse.
        return authomatic.core.UserInfoResponse(response, self.user)
    
    
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
    
    #: Indicates whether the **provider** supports access to
    #: **user's** protected resources.
    has_protected_resources = False
    
    def __init__(self, *args, **kwargs):   
        super(AuthenticationProvider, self).__init__(*args, **kwargs)
        
        self.identifier_param = kwargs.get('identifier_param', 'id')
        
        self.identifier = authomatic.core.mw.params.get(self.identifier_param)
        
        
        












