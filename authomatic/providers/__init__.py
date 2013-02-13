"""
Base Providers
--------------

This module provides abstract classes for implementation of protocol specific abstract classes.

.. autosummary::
    
    login_decorator
    BaseProvider
    AuthorisationProvider
    AuthenticationProvider

"""

from authomatic.exceptions import ConfigError, AuthenticationError
import abc
import authomatic.core
import datetime
import hashlib
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
    
    def __init__(self, adapter, config, provider_name, callback=None,
                 report_errors=True, logging_level=logging.INFO,
                 prefix='authomatic', **kwargs):
        
        #: The :doc:`platform adapter <adapters>`.
        self.adapter = adapter
        
        #: :doc:`config`
        self.config = config
        
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
    
    
    #=======================================================================
    # Abstract properties
    #=======================================================================
    
    @abc.abstractproperty
    def has_protected_resources(self):
        """
        :class:`bool` Indicates whether the **provider** supports access to
        **user's** protected resources.  
        """
    
    
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
        
        return self.config.get(self.name, {}).get(kwname) or kwargs.get(kwname) or default
    
    
    def _session_key(self, key):
        """
        Generates session key string.
        
        :param str key:
            e.g. ``"authomatic:facebook:key"``
        """
        
        return '{}:{}:{}'.format(self.prefix, self.name, key)
    
    
    def _session_set(self, key, value):
        """Saves a value to session."""
        
        self.adapter.session[self._session_key(key)] = value
    
    
    def _session_get(self, key):
        """Retrieves a value from session."""
        return self.adapter.session[self._session_key(key)]
    
    
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
        
    
    def _fetch(self, *args, **kwargs):
        """
        Fetches a url.
        
        A wrapper around :meth:`.adapters.BaseAdapter.fetch_async` method.
        """
        
        return self.adapter.fetch_async(*args, **kwargs).get_response()
        
    
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
    
    #: Indicates whether the **provider** supports access to
    #: **user's** protected resources.
    has_protected_resources = True
    
    USER_AUTHORISATION_REQUEST_TYPE = 2
    ACCESS_TOKEN_REQUEST_TYPE = 3
    PROTECTED_RESOURCE_REQUEST_TYPE = 4
    
    def __init__(self, *args, **kwargs):
        super(AuthorisationProvider, self).__init__(*args, **kwargs)
        
        #: :class:`.core.Consumer`
        self.consumer = self._kwarg(kwargs, 'consumer')
#        self.consumer = kwargs.get('consumer')
        
        #: Short name as specified in the :doc:`config`.
        self.short_name = self._kwarg(kwargs, 'short_name')
#        self.short_name = self.adapter.config.get(self.name, {}).get('short_name')
    
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
    
    @abc.abstractmethod
    def fetch_protected_resource(self, adapter, url, credentials, content_parser,
                                 method='GET', headers={}, response_parser=None):
        """
        Fetches protected resource asynchronously.
           
        .. warning:: |async|
        
        :param adapter:
            The same :doc:`adapter <adapters>` instance which was used in the :func:`authomatic.login`
            function to get the **user's** :class:`.core.Credentials`.
        :param core.Credentials credentials:
            :class:`Credentials <.core.Credentials>` of the **user** whose
            **protected resource** we want to access.
        :param str url:
            URL of the protected resource. Can contain query parameters.
        :param str method:
            HTTP method of the request.
        :param callable content_parser:
            A :class:`callable` as described in :attr:`core.Response.content_parser`.
        
        :returns:
            :class:`.adapters.RPC`
        """
    
    
    #===========================================================================
    # Exposed methods
    #===========================================================================
    
    def create_request(self, url, method='GET', content_parser=None, response_parser=None):
        """
        Creates an authorized :class:`request <.core.Request>` to **protected resources** of a **user**.
        
        :param str url:
            URL of the protected resource. Can contain query parameters.
        :param str method:
            HTTP method of the request.
        :param callable content_parser:
            A callable as described in :attr:`.core.Response.content_parser`.
        :param callable response_parser:            
            A callable as described in :attr:`.core.Request.response_parser`.
        
        :returns:
            :class:`.core.Request`
        """
        
        return authomatic.core.Request(adapter=self.adapter,
                                       config=self.config,
                                       credentials=self.user.credentials,
                                       url=url,
                                       method=method,
                                       content_parser=content_parser,
                                       response_parser=response_parser)
        
    
    def fetch_user_info(self):
        """
        Makes **synchronous** request to :attr:`.user_info_url` and
        returns the :class:`.core.UserInfoResponse`.
        
        :returns:
            :class:`.core.UserInfoResponse`
        """
        
        return self.user_info_request.fetch().get_response()
    
    
    def update_user(self):
        """
        Updates the :attr:`user <.BaseProvider.user>`.
        
        .. warning::
        
            Makes a request to :attr:`.user_info_url`!
        
        :returns:
            :class:`.core.User`
        """
        
        return self.fetch_user_info().user
    
    
    @property
    def user_info_request(self):
        """
        Returns an **asynchronous** :class:`request <.core.Request>` to :attr:`.user_info_url`
        whose :meth:`get_response() <.core.Request.get_response>` method returns
        a :class:`.core.UserInfoResponse`.
        
        :returns:
            :class:`.core.Request`
        """
        
        if not self._user_info_request:
            
            def response_parser(response, content_parser):
                """
                Response parser which converts response to :class:`.core.UserInfoResponse`.
                """
                
                # Parse response.
                response = self.adapter.response_parser(response, content_parser)
                
                # Create user.
                self.user = self._update_or_create_user(response.data)
                
                # Return UserInfoResponse.
                return authomatic.core.UserInfoResponse(response, self.user)
            
            # Create the request
            self._user_info_request = self.create_request(self.user_info_url,
                                                          response_parser=response_parser)
        
        return self._user_info_request
    
    
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
    
    #: :class:`str` The *claimed identity* of a **user**.
    identifier = ''
    
    #: Indicates whether the **provider** supports access to
    #: **user's** protected resources.
    has_protected_resources = False
    
    def __init__(self, *args, **kwargs):   
        super(AuthenticationProvider, self).__init__(*args, **kwargs)
        
        # takes the identifier keyword argument into account only if the identifier is not hardcoded
#        self.identifier = self.identifier or kwargs.get('identifier')
        
        self.identifier_param = kwargs.get('identifier_param', 'id')
        
        self.identifier = self.adapter.params.get(self.identifier_param)
        
        
        












