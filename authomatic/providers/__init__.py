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
    AuthorizationProvider
    AuthenticationProvider

"""

import abc
import base64
import hashlib
import logging
import random
import sys
import traceback
import uuid

import authomatic.core
from authomatic.exceptions import (
    ConfigError,
    FetchError,
    CredentialsError,
)
from authomatic import six
from authomatic.six.moves import urllib_parse as parse
from authomatic.six.moves import http_client
from authomatic.exceptions import CancellationError

__all__ = [
    'BaseProvider',
    'AuthorizationProvider',
    'AuthenticationProvider',
    'login_decorator']


def _error_traceback_html(exc_info, traceback_):
    """
    Generates error traceback HTML.

    :param tuple exc_info:
        Output of :func:`sys.exc_info` function.

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

    return html.format(error=exc_info[1], traceback=traceback_)


def login_decorator(func):
    """
    Decorate the :meth:`.BaseProvider.login` implementations with this
    decorator.

    Provides mechanism for error reporting and returning result which
    makes the :meth:`.BaseProvider.login` implementation cleaner.

    """

    def wrap(provider, *args, **kwargs):
        error = None
        result = authomatic.core.LoginResult(provider)

        try:
            func(provider, *args, **kwargs)
        except Exception as e:  # pylint:disable=broad-except
            if provider.settings.report_errors:
                error = e
                if not isinstance(error, CancellationError):
                    provider._log(
                        logging.ERROR,
                        u'Reported suppressed exception: {0}!'.format(
                            repr(error)),
                        exc_info=1)
            else:
                if provider.settings.debug:
                    # TODO: Check whether it actually works without middleware
                    provider.write(
                        _error_traceback_html(
                            sys.exc_info(),
                            traceback.format_exc()))
                raise

        # If there is user or error the login procedure has finished
        if provider.user or error:
            result = authomatic.core.LoginResult(provider)
            # Add error to result
            result.error = error

            # delete session cookie
            if isinstance(provider.session, authomatic.core.Session):
                provider.session.delete()

            provider._log(logging.INFO, u'Procedure finished.')

            if provider.callback:
                provider.callback(result)
            return result
        else:
            # Save session
            provider.save_session()

    return wrap


class BaseProvider(object):
    """
    Abstract base class for all providers.
    """

    PROVIDER_TYPE_ID = 0

    _repr_ignore = ('user',)

    __metaclass__ = abc.ABCMeta

    supported_user_attributes = authomatic.core.SupportedUserAttributes()

    def __init__(self, settings, adapter, provider_name, session=None,
                 session_saver=None, callback=None, js_callback=None,
                 prefix='authomatic', **kwargs):

        self.settings = settings
        self.adapter = adapter

        self.session = session
        self.save_session = session_saver

        #: :class:`str` The provider name as specified in the :doc:`config`.
        self.name = provider_name

        #: :class:`callable` An optional callback called when the login
        #: procedure is finished with :class:`.core.LoginResult` passed as
        #: argument.
        self.callback = callback

        #: :class:`str` Name of an optional javascript callback.
        self.js_callback = js_callback

        #: :class:`.core.User`.
        self.user = None

        #: :class:`bool` If ``True``, the
        #: :attr:`.BaseProvider.user_authorization_url` will be displayed
        #: in a *popup mode*, if the **provider** supports it.
        self.popup = self._kwarg(kwargs, 'popup')

    @property
    def url(self):
        return self.adapter.url

    @property
    def params(self):
        return self.adapter.params

    def write(self, value):
        self.adapter.write(value)

    def set_header(self, key, value):
        self.adapter.set_header(key, value)

    def set_status(self, status):
        self.adapter.set_status(status)

    def redirect(self, url):
        self.set_status('302 Found')
        self.set_header('Location', url)

    # ========================================================================
    # Abstract methods
    # ========================================================================

    @abc.abstractmethod
    def login(self):
        """
        Launches the *login procedure* to get **user's credentials** from
        **provider**.

        Should be decorated with :func:`.login_decorator`. The *login
        procedure* is considered finished when the :attr:`.user`
        attribute is not empty when the method runs out of it's flow or
        when there are errors.

        """

    # ========================================================================
    # Exposed methods
    # ========================================================================

    def to_dict(self):
        """
        Converts the provider instance to a :class:`dict`.

        :returns:
            :class:`dict`

        """

        return dict(name=self.name,
                    id=getattr(self, 'id', None),
                    type_id=self.type_id,
                    type=self.get_type(),
                    scope=getattr(self, 'scope', None),
                    user=self.user.id if self.user else None)

    @classmethod
    def get_type(cls):
        """
        Returns the provider type.

        :returns:
            :class:`str` The full dotted path to base class e.g.
            :literal:`"authomatic.providers.oauth2.OAuth2"`.

        """

        return cls.__module__ + '.' + cls.__bases__[0].__name__

    def update_user(self):
        """
        Updates and returns :attr:`.user`.

        :returns:
            :class:`.User`

        """

    # ========================================================================
    # Internal methods
    # ========================================================================

    @property
    def type_id(self):
        pass

    def _kwarg(self, kwargs, kwname, default=None):
        """
        Resolves keyword arguments from constructor or :doc:`config`.

        .. note::

            The keyword arguments take this order of precedence:

            1. Arguments passed to constructor through the
               :func:`authomatic.login`.
            2. Provider specific arguments from :doc:`config`.
            3. Arguments from :doc:`config` set in the ``__defaults__`` key.
            2. The value from :data:`default` argument.

        :param dict kwargs:
            Keyword arguments dictionary.
        :param str kwname:
            Name of the desired keyword argument.

        """

        return kwargs.get(kwname) or \
            self.settings.config.get(self.name, {}).get(kwname) or \
            self.settings.config.get('__defaults__', {}).get(kwname) or \
            default

    def _session_key(self, key):
        """
        Generates session key string.

        :param str key:
            e.g. ``"authomatic:facebook:key"``

        """

        return '{0}:{1}:{2}'.format(self.settings.prefix, self.name, key)

    def _session_set(self, key, value):
        """
        Saves a value to session.
        """

        self.session[self._session_key(key)] = value

    def _session_get(self, key):
        """
        Retrieves a value from session.
        """

        return self.session.get(self._session_key(key))

    @staticmethod
    def csrf_generator(secret):
        """
        Generates CSRF token.

        Inspired by this article:
        http://blog.ptsecurity.com/2012/10/random-number-security-in-python.html

        :returns:
            :class:`str` Random unguessable string.

        """

        # Create hash from random string plus salt.
        hashed = hashlib.md5(uuid.uuid4().bytes + six.b(secret)).hexdigest()

        # Each time return random portion of the hash.
        span = 5
        shift = random.randint(0, span)
        return hashed[shift:shift - span - 1]

    @classmethod
    def _log(cls, level, msg, **kwargs):
        """
        Logs a message with pre-formatted prefix.

        :param int level:
            Logging level as specified in the
            `login module <http://docs.python.org/2/library/logging.html>`_ of
            Python standard library.

        :param str msg:
            The actual message.

        """

        logger = getattr(cls, '_logger', None) or authomatic.core._logger
        logger.log(
            level, ': '.join(
                ('authomatic', cls.__name__, msg)), **kwargs)

    def _fetch(self, url, method='GET', params=None, headers=None,
               body='', max_redirects=5, content_parser=None):
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

        :param str body:
            Body of ``POST``, ``PUT`` and ``PATCH`` requests.

        :param int max_redirects:
            Number of maximum HTTP redirects to follow.

        :param function content_parser:
            A callable to be used to parse the :attr:`.Response.data`
            from :attr:`.Response.content`.

        """
        # 'magic' using _kwarg method
        # pylint:disable=no-member
        params = params or {}
        params.update(self.access_params)

        headers = headers or {}
        headers.update(self.access_headers)

        scheme, host, path, query, fragment = parse.urlsplit(url)
        query = parse.urlencode(params)

        if method in ('POST', 'PUT', 'PATCH'):
            if not body:
                # Put querystring to body
                body = query
                query = ''
                headers.update(
                    {'Content-Type': 'application/x-www-form-urlencoded'})
        request_path = parse.urlunsplit(('', '', path or '', query or '', ''))

        self._log(logging.DEBUG, u' \u251C\u2500 host: {0}'.format(host))
        self._log(
            logging.DEBUG,
            u' \u251C\u2500 path: {0}'.format(request_path))
        self._log(logging.DEBUG, u' \u251C\u2500 method: {0}'.format(method))
        self._log(logging.DEBUG, u' \u251C\u2500 body: {0}'.format(body))
        self._log(logging.DEBUG, u' \u251C\u2500 params: {0}'.format(params))
        self._log(logging.DEBUG, u' \u2514\u2500 headers: {0}'.format(headers))

        # Connect
        if scheme.lower() == 'https':
            connection = http_client.HTTPSConnection(host)
        else:
            connection = http_client.HTTPConnection(host)

        try:
            connection.request(method, request_path, body, headers)
        except Exception as e:
            original_message = e.message if hasattr(e, 'message') else str(e)
            raise FetchError(message,
                             original_message=original_message,
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

                self._log(logging.DEBUG, u'Redirecting to {0}'.format(url))
                self._log(logging.DEBUG, u'Remaining redirects: {0}'
                          .format(remaining_redirects))

                # Call this method again.
                response = self._fetch(url=location,
                                       params=params,
                                       method=method,
                                       headers=headers,
                                       max_redirects=remaining_redirects)

            else:
                raise FetchError('Max redirects reached!',
                                 url=location,
                                 status=response.status)
        else:
            self._log(logging.DEBUG, u'Got response:')
            self._log(logging.DEBUG, u' \u251C\u2500 url: {0}'.format(url))
            self._log(
                logging.DEBUG,
                u' \u251C\u2500 status: {0}'.format(
                    response.status))
            self._log(
                logging.DEBUG,
                u' \u2514\u2500 headers: {0}'.format(
                    response.getheaders()))

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
        for key in self.user.__dict__:
            # Exclude data.
            if key not in ('data', 'content'):
                # Extract every data item whose key matches the user
                # property name, but only if it has a value.
                value = data.get(key)
                if value:
                    setattr(self.user, key, value)

        # Handle different structure of data by different providers.
        self.user = self._x_user_parser(self.user, data)

        if self.user.id:
            self.user.id = str(self.user.id)

        # TODO: Move to User
        # If there is no user.name,
        if not self.user.name:
            if self.user.first_name and self.user.last_name:
                # Create it from first name and last name if available.
                self.user.name = ' '.join((self.user.first_name,
                                           self.user.last_name))
            else:
                # Or use one of these.
                self.user.name = (self.user.username or self.user.nickname or
                                  self.user.first_name or self.user.last_name)

        if not self.user.location:
            if self.user.city and self.user.country:
                self.user.location = '{0}, {1}'.format(self.user.city,
                                                       self.user.country)
            else:
                self.user.location = self.user.city or self.user.country

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

    @staticmethod
    def _http_status_in_category(status, category):
        """
        Checks whether a HTTP status code is in the category denoted by the
        hundreds digit.
        """

        assert category < 10, 'HTTP status category must be a one-digit int!'
        cat = category * 100
        return status >= cat and status < cat + 100


class AuthorizationProvider(BaseProvider):
    """
    Base provider for *authorization protocols* i.e. protocols which allow a
    **provider** to authorize a **consumer** to access **protected resources**
    of a **user**.

    e.g. `OAuth 2.0 <http://oauth.net/2/>`_ or `OAuth 1.0a
    <http://oauth.net/core/1.0a/>`_.

    """

    USER_AUTHORIZATION_REQUEST_TYPE = 2
    ACCESS_TOKEN_REQUEST_TYPE = 3
    PROTECTED_RESOURCE_REQUEST_TYPE = 4
    REFRESH_TOKEN_REQUEST_TYPE = 5

    BEARER = 'Bearer'

    _x_term_dict = {}

    #: If ``True`` the provider doesn't support Cross-site HTTP requests.
    same_origin = True

    #: :class:`bool` Whether the provider supports JSONP requests.
    supports_jsonp = False

    # Whether to use the HTTP Authorization header.
    _x_use_authorization_header = True

    def __init__(self, *args, **kwargs):
        """
        Accepts additional keyword arguments:

        :arg str consumer_key:
            The *key* assigned to our application (**consumer**) by the
            **provider**.

        :arg str consumer_secret:
            The *secret* assigned to our application (**consumer**) by the
            **provider**.

        :arg int id:
            A unique numeric ID used to serialize :class:`.Credentials`.

        :arg dict user_authorization_params:
            A dictionary of additional request parameters for
            **user authorization request**.

        :arg dict access_token_params:
            A dictionary of additional request parameters for
            **access_with_credentials token request**.

        :arg dict access_headers:
            A dictionary of default HTTP headers that will be used when
            accessing **user's** protected resources.
            Applied by :meth:`.access()`, :meth:`.update_user()` and
            :meth:`.User.update()`

        :arg dict access_params:
            A dictionary of default query string parameters that will be used
            when accessing **user's** protected resources.
            Applied by :meth:`.access()`, :meth:`.update_user()` and
            :meth:`.User.update()`

        """

        super(AuthorizationProvider, self).__init__(*args, **kwargs)

        self.consumer_key = self._kwarg(kwargs, 'consumer_key')
        self.consumer_secret = self._kwarg(kwargs, 'consumer_secret')

        self.user_authorization_params = self._kwarg(
            kwargs, 'user_authorization_params', {})

        self.access_token_headers = self._kwarg(
            kwargs, 'user_authorization_headers', {})
        self.access_token_params = self._kwarg(
            kwargs, 'access_token_params', {})

        self.id = self._kwarg(kwargs, 'id')

        self.access_headers = self._kwarg(kwargs, 'access_headers', {})
        self.access_params = self._kwarg(kwargs, 'access_params', {})

        #: :class:`.Credentials` to access **user's protected resources**.
        self.credentials = authomatic.core.Credentials(
            self.settings.config, provider=self)

        #: Response of the *access token request*.
        self.access_token_response = None

    # ========================================================================
    # Abstract properties
    # ========================================================================

    @abc.abstractproperty
    def user_authorization_url(self):
        """
        :class:`str` URL to which we redirect the **user** to grant our app
        i.e. the **consumer** an **authorization** to access his
        **protected resources**. See
        http://tools.ietf.org/html/rfc6749#section-4.1.1 and
        http://oauth.net/core/1.0a/#auth_step2.
        """

    @abc.abstractproperty
    def access_token_url(self):
        """
        :class:`str` URL where we can get the *access token* to access
        **protected resources** of a **user**. See
        http://tools.ietf.org/html/rfc6749#section-4.1.3 and
        http://oauth.net/core/1.0a/#auth_step3.
        """

    @abc.abstractproperty
    def user_info_url(self):
        """
        :class:`str` URL where we can get the **user** info.
        see http://tools.ietf.org/html/rfc6749#section-7 and
        http://oauth.net/core/1.0a/#anchor12.
        """

    # ========================================================================
    # Abstract methods
    # ========================================================================

    @abc.abstractmethod
    def to_tuple(self, credentials):
        """
        Must convert :data:`credentials` to a :class:`tuple` to be used by
        :meth:`.Credentials.serialize`.

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
        Must convert the :data:`deserialized_tuple` back to
        :class:`.Credentials`.

        .. warning::

            |classmethod|

        :param tuple deserialized_tuple:
            A tuple whose first index is the :attr:`.id` and the rest
            are all the items of the :class:`tuple` created by
            :meth:`.to_tuple`.

        :param credentials:
            A :class:`.Credentials` instance.

        :param dict cfg:
            Provider configuration from :doc:`config`.

        """

    @abc.abstractmethod
    def create_request_elements(self, request_type, credentials,
                                url, method='GET', params=None, headers=None,
                                body=''):
        """
        Must return :class:`.RequestElements`.

        .. warning::

            |classmethod|

        :param int request_type:
            Type of the request specified by one of the class's constants.

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

        :param str body:
            Body of ``POST``, ``PUT`` and ``PATCH`` requests.

        :returns:
            :class:`.RequestElements`

        """

    # ========================================================================
    # Exposed methods
    # ========================================================================

    @property
    def type_id(self):
        """
        A short string representing the provider implementation id used for
        serialization of :class:`.Credentials` and to identify the type of
        provider in JavaScript.

        The part before hyphen denotes the type of the provider, the part
        after hyphen denotes the class id e.g.
        ``oauth2.Facebook.type_id = '2-5'``,
        ``oauth1.Twitter.type_id = '1-5'``.

        """

        cls = self.__class__
        mod = sys.modules.get(cls.__module__)

        return str(self.PROVIDER_TYPE_ID) + '-' + \
            str(mod.PROVIDER_ID_MAP.index(cls))

    def access(self, url, params=None, method='GET', headers=None,
               body='', max_redirects=5, content_parser=None):
        """
        Fetches the **protected resource** of an authenticated **user**.

        :param credentials:
            The **user's** :class:`.Credentials` (serialized or normal).

        :param str url:
            The URL of the **protected resource**.

        :param str method:
            HTTP method of the request.

        :param dict headers:
            HTTP headers of the request.

        :param str body:
            Body of ``POST``, ``PUT`` and ``PATCH`` requests.

        :param int max_redirects:
            Maximum number of HTTP redirects to follow.

        :param function content_parser:
            A function to be used to parse the :attr:`.Response.data`
            from :attr:`.Response.content`.

        :returns:
            :class:`.Response`

        """

        if not self.user and not self.credentials:
            raise CredentialsError(u'There is no authenticated user!')

        headers = headers or {}

        self._log(
            logging.INFO,
            u'Accessing protected resource {0}.'.format(url))

        request_elements = self.create_request_elements(
            request_type=self.PROTECTED_RESOURCE_REQUEST_TYPE,
            credentials=self.credentials,
            url=url,
            body=body,
            params=params,
            headers=headers,
            method=method
        )

        response = self._fetch(*request_elements,
                               max_redirects=max_redirects,
                               content_parser=content_parser)

        self._log(
            logging.INFO,
            u'Got response. HTTP status = {0}.'.format(
                response.status))
        return response

    def async_access(self, *args, **kwargs):
        """
        Same as :meth:`.access` but runs asynchronously in a separate thread.

        .. warning::

            |async|

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
            response = self._access_user_info()
            self.user = self._update_or_create_user(response.data,
                                                    content=response.content)
            return authomatic.core.UserInfoResponse(self.user,
                                                    response.httplib_response)

    # ========================================================================
    # Internal methods
    # ========================================================================

    @classmethod
    def _authorization_header(cls, credentials):
        """
        Creates authorization headers if the provider supports it. See:
        http://en.wikipedia.org/wiki/Basic_access_authentication.

        :param credentials:
            :class:`.Credentials`

        :returns:
            Headers as :class:`dict`.

        """

        if cls._x_use_authorization_header:
            res = ':'.join(
                (credentials.consumer_key,
                 credentials.consumer_secret))
            res = base64.b64encode(six.b(res)).decode()
            return {'Authorization': 'Basic {0}'.format(res)}
        else:
            return {}

    def _check_consumer(self):
        """
        Validates the :attr:`.consumer`.
        """

        # 'magic' using _kwarg method
        # pylint:disable=no-member
        if not self.consumer.key:
            raise ConfigError(
                'Consumer key not specified for provider {0}!'.format(
                    self.name))

        if not self.consumer.secret:
            raise ConfigError(
                'Consumer secret not specified for provider {0}!'.format(
                    self.name))

    @staticmethod
    def _split_url(url):
        """
        Splits given url to url base and params converted to list of tuples.
        """

        split = parse.urlsplit(url)
        base = parse.urlunsplit((split.scheme, split.netloc, split.path, 0, 0))
        params = parse.parse_qsl(split.query, True)

        return base, params

    @classmethod
    def _x_request_elements_filter(
            cls, request_type, request_elements, credentials):
        """
        Override this to handle special request requirements of zealous
        providers.

        .. warning::

            |classmethod|

        :param int request_type:
            Type of request.

        :param request_elements:
            :class:`.RequestElements`

        :param credentials:
            :class:`.Credentials`

        :returns:
            :class:`.RequestElements`

        """

        return request_elements

    @staticmethod
    def _x_credentials_parser(credentials, data):
        """
        Override this to handle differences in naming conventions across
        providers.

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
        return self.access(url)


class AuthenticationProvider(BaseProvider):
    """
    Base provider for *authentication protocols* i.e. protocols which allow a
    **provider** to authenticate a *claimed identity* of a **user**.

    e.g. `OpenID <http://openid.net/>`_.

    """

    #: Indicates whether the **provider** supports access_with_credentials to
    #: **user's** protected resources.
    # TODO: Useless
    has_protected_resources = False

    def __init__(self, *args, **kwargs):
        super(AuthenticationProvider, self).__init__(*args, **kwargs)

        # Lookup default identifier, if available in provider
        default_identifier = getattr(self, 'identifier', None)

        # Allow for custom name for the "id" querystring parameter.
        self.identifier_param = kwargs.get('identifier_param', 'id')

        # Get the identifier from request params, or use default as fallback.
        self.identifier = self.params.get(
            self.identifier_param, default_identifier)


PROVIDER_ID_MAP = [
    AuthenticationProvider,
    AuthorizationProvider,
    BaseProvider,
]
