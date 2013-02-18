#TODO: Add coding line to all modules
# -*- coding: utf-8 -*-
from urllib import urlencode
import binascii
import datetime
import exceptions
import hashlib
import hmac
import logging
import pickle
import providers
import random
import sys
import time
import urllib
import urlparse


# Taken from anyjson.py
try:
    import simplejson as json
except ImportError:
    try:
        # Try to import from django, should work on Google App Engine.
        from django.utils import simplejson as json
    except ImportError:
        # Should work for Python2.6 and higher.
        import json


class ReprMixin(object):
    """
    Provides __repr__() method with output *ClassName(arg1=value, arg2=value)*.
    
    Ignored are attributes
    
    * which values are considered false.
    * with leading underscore.
    * listed in _repr_ignore.
    
    Values of attributes listed in _repr_sensitive will be replaced by *###*.
    Values which repr() string is longer than _repr_lenght_limit will be represented as *ClassName(...)*
    """
    
    #: Iterable of attributes to be ignored.
    _repr_ignore = []
    #: Iterable of attributes which value should not be visible.
    _repr_sensitive = []
    #: `int` Values longer than this will be truncated to *ClassName(...)*.
    _repr_lenght_limit = 20
    
    
    def __repr__(self):
        
        # get class name
        name = self.__class__.__name__
        
        # construct keyword arguments
        args = []
        
        for k, v in self.__dict__.items():
            
            # ignore attributes with leading underscores and those listed in _repr_ignore
            if v and not k.startswith('_') and not k in self._repr_ignore:
                
                # replace sensitive values
                if k in self._repr_sensitive:
                    v = '###'
                
                # if repr is too long
                if len(repr(v)) > self._repr_lenght_limit:
                    # Truncate to ClassName(...)
                    v = '{}(...)'.format(v.__class__.__name__)
                else:
                    v = repr(v)
                
                args.append('{}={}'.format(k, v))
        
        args = ', '.join(args)
        
        return '{}({})'.format(name, args)


def login(adapter, config, provider_name, callback=None, report_errors=True,
          logging_level=logging.DEBUG, **kwargs):
    """
    Launches a login procedure for specified :doc:`provider <providers>` and returns :class:`.LoginResult`.
    
    .. warning::
        Currently the method gets called twice by all :doc:`providers <providers>`. This may change in future.
        
        #. First it returns nothing but redirects the **user** to the **provider**,
           which redirects him back to the enclosing **request handler**.
        #. Then it gets called again and it finally returns the :class:`.LoginResult`
           or calls the function specified in the ``callback`` argument with
           :class:`.LoginResult` passed as argument.
    
    :param adapter:
        Framework specific :doc:`adapter <adapters>`.
    :param dict config:
        :doc:`config`
    :param str provider_name:
        Name of the provider as specified in the keys of the :doc:`config`.
    :param callable callback:
        If specified the function will call the callback with :class:`.LoginResult`
        passed as argument and will return nothing.
    :param bool report_errors:
        If ``True`` errors and exceptions which occur during login will be caught and
        accessible in the :class:`.LoginResult`.
        If ``False`` errors and exceptions will not be handled.
    :param int logging_level:
        The library logs important events during the login procedure.
        You can specify the desired logging level with the constants of the
        `logging <http://docs.python.org/2/library/logging.html>`_ of Python standard library.
        The main login procedure events have level ``INFO``, others like adapter database access
        have level ``DEBUG``.
        
    .. note::
        
        Accepts other :doc:`provider <providers>` specific keyword arguments.
    
    :returns:
        :obj:`None` or :class:`.LoginResult`.
    """
    
    # retrieve required settings for current provider and raise exceptions if missing
    provider_settings = config.get(provider_name)
    if not provider_settings:
        raise exceptions.ConfigError('Provider name "{}" not specified!'.format(provider_name))
    
    class_ = provider_settings.get('class_')
    if not class_:
        raise exceptions.ConfigError('The "class_" key not specified in the config for provider {}!'.format(provider_name))
    
    ProviderClass = resolve_provider_class(class_)
    
    # instantiate provider class
    provider = ProviderClass(adapter, config, provider_name, callback,
                             report_errors=report_errors,
                             logging_level=logging_level,
                             **kwargs)
    
    # return login result
    return provider.login()


class Counter(object):
    """
    A simple counter to be used in the config to generate unique `short_name` values.
    """
    
    def __init__(self, start=0):
        self._count = start
        
    def count(self):
        self._count += 1
        return self._count

#: A simple counter to be used in the config to generate unique `short_name` values.
_counter = Counter()

def short_name():
    """
    A simple counter to be used in the config to generate unique `short_name` values.
    
    :returns:
        :class:`int`.
     
    Use it in the :doc:`config` like this:
    ::
    
        import authomatic
        
        CONFIG = {
            'facebook': {
                 'class_': authomatic.providers.oauth2.Facebook,
                 'short_name': authomatic.short_name(), # returns 1
                 'consumer_key': '##########',
                 'consumer_secret': '##########',
                 'scope': ['user_about_me', 'email']
            },
            'google': {
                 'class_': 'authomatic.providers.oauth2.Google',
                 'short_name': authomatic.short_name(), # returns 2
                 'consumer_key': '##########',
                 'consumer_secret': '##########',
                 'scope': ['https://www.googleapis.com/auth/userinfo.profile',
                           'https://www.googleapis.com/auth/userinfo.email']
            },
            'windows_live': {
                 'class_': 'oauth2.WindowsLive',
                 'short_name': authomatic.short_name(), # returns 3
                 'consumer_key': '##########',
                 'consumer_secret': '##########',
                 'scope': ['wl.basic', 'wl.emails', 'wl.photos']
            },
        }
    """
    
    return _counter.count()


def escape(s):
    """Escape a URL including any /."""
    return urllib.quote(s.encode('utf-8'), safe='~')


def resolve_provider_class(class_):
    """
    Returns a provider class. 
    
    :param class_name: :class:`string` or :class:`authomatic.providers.BaseProvider` subclass.
    """
    
    if type(class_) in (str, unicode):
        # prepare path for authomatic.providers package
        path = '.'.join([__package__, 'providers', class_])
        
        # try to import class by string from providers module or by fully qualified path
        return import_string(class_, True) or import_string(path)
    else:
        return class_


def import_string(import_name, silent=False):
    """
    Imports an object by string in dotted notation.
    
    taken `from webapp2.import_string() <http://webapp-improved.appspot.com/api/webapp2.html#webapp2.import_string>`_
    """
    
    try:
        if '.' in import_name:
            module, obj = import_name.rsplit('.', 1)
            return getattr(__import__(module, None, None, [obj]), obj)
        else:
            return __import__(import_name)
    except (ImportError, AttributeError), e:
        if not silent:
            raise exceptions.ImportStringError('Import from string failed for path {}'.format(import_name),
                                               str(e))


def short_name_to_name(config, short_name):
    """
    Returns the provider :doc:`config` key based on it's
    ``short_name`` value.
    
    :param dict config:
        :doc:`config`.
    :param short_name:
        Value of the short_name parameter in the :ref:`config` to search for.
    """
    
    for k, v in config.items():
        if v.get('short_name') == short_name:
            return k
            break
    else:
        raise Exception('No provider with short_name={} found in the config!'.format(short_name))


class User(ReprMixin):
    """
    Provides unified interface to selected **user** informations returned by different **providers**.
    
    .. note:: The format of property values may vary across providers.
    """
    
    def __init__(self, provider, **kwargs):
        #: A :doc:`provider <providers>` instance.
        self.provider = provider
        
        #: An :class:`.Credentials` instance.
        self.credentials = kwargs.get('credentials')
        
        #: A :class:`dict` containing all the **user** information returned by the **provider**.
        #: The structure differs across **providers**.
        self.raw_user_info = kwargs.get('raw_user_info')
        
        #: :class:`str` ID assigned to the **user** by the **provider**.
        self.id = kwargs.get('id')
        #: :class:`str` User name e.g. *andrewpipkin*.
        self.username = kwargs.get('username')
        #: :class:`str` Name e.g. *Andrew Pipkin*.
        self.name = kwargs.get('name')
        #: :class:`str` First name e.g. *Andrew*.
        self.first_name = kwargs.get('first_name')
        #: :class:`str` Last name e.g. *Pipkin*.
        self.last_name = kwargs.get('last_name')
        #: :class:`str` Nickname e.g. *Andy*.
        self.nickname = kwargs.get('nickname')
        #: :class:`str` Link URL.
        self.link = kwargs.get('link')
        #: :class:`str` Gender.
        self.gender = kwargs.get('gender')
        #: :class:`str` Timezone.
        self.timezone = kwargs.get('timezone')
        #: :class:`str` Locale.
        self.locale = kwargs.get('locale')
        #: :class:`str` E-mail.
        self.email = kwargs.get('email')
        #: :class:`str` Picture URL.
        self.picture = kwargs.get('picture')
        #: :class:`datetime.datetime()` birth date .
        self.birth_date = kwargs.get('birth_date')
        #: :class:`str` Country.
        self.country = kwargs.get('country')
        #: :class:`str` Postal code.
        self.postal_code = kwargs.get('postal_code')
        #: Instance of the Google App Engine Users API
        #: `User <https://developers.google.com/appengine/docs/python/users/userclass>`_ class.
        #: Only present when using the :class:`authomatic.providers.gaeopenid.GAEOpenID` provider.
        self.gae_user = kwargs.get('gae_user')
    
    
    def update(self):
        """
        Updates the user info by fetching the **provider's** user info URL.
        
        :returns:
            Updated instance of this class.
        """
        
        return self.provider.update_user()


class Credentials(ReprMixin):
    """Contains all neccessary informations to fetch **user's protected resources**."""
    
    _repr_sensitive = ('token', 'token_secret', 'consumer_key', 'consumer_secret')
    
    def __init__(self, **kwargs):
        
        #: :class:`str` User **access token**.
        self.token = kwargs.get('token')
        
        #: :class:`str` User **access token secret**.
        self.token_secret = kwargs.get('token_secret')
        
        #: :class:`datetime.datetime()` Expiration date of the **access token**.
        self.expiration_date = kwargs.get('expiration_date')
        
        #: A :doc:`Provider <providers>` instance**.
        provider = kwargs.get('provider')
        
        self._expires_in = kwargs.get('expires_in', 0)
        
        if provider:
            #: :class:`str` Provider name specified in the :doc:`config`.
            self.provider_name = provider.name
            #: :class:`str` Provider type e.g. ``"authomatic.providers.oauth2.OAuth2"``.
            self.provider_type = provider.get_type()
            #: :class:`str` Provider short name specified in the :doc:`config`.
            self.provider_short_name = provider.short_name
            #: :class:`str` Consumer key specified in the :doc:`config`.
            self.consumer_key = provider.consumer_key
            #: :class:`str` Consumer secret specified in the :doc:`config`.
            self.consumer_secret = provider.consumer_secret
        else:
            self.provider_name = kwargs.get('provider_name')
            self.provider_type = kwargs.get('provider_type')
            self.provider_short_name = kwargs.get('provider_short_name')
            
            self.consumer_key = kwargs.get('consumer_key')
            self.consumer_secret = kwargs.get('consumer_secret')
    
    
    @property
    def expires_in(self):
        if self._expires_in:
            return self._expires_in
        else:
            None
    
    
    @expires_in.setter
    def expires_in(self, value):
        if value:
            self.expiration_date = datetime.datetime.now() + datetime.timedelta(seconds=int(value))
            self._expires_in = value
    
    
    @property
    def valid(self):
        """
        ``True`` if credentials are valid, ``False`` if expired.
        """
        if self.expiration_date:
            return self.expiration_date > datetime.datetime.now()
        else:
            return True
    
    
    def expires_soon(self, *args, **kwargs):
        """
        Returns ``True`` if credentials expire sooner than specified.
        The method has the same signature as :func:`datetime.timedelta`.
        
        :returns:
            ``True`` if credentials expire sooner than specified, else ``False``.
        """
        
        if self.expiration_date:
            return self.expiration_date < datetime.datetime.now() + datetime.timedelta(*args, **kwargs)
        else:
            return False
    
    
    def get_provider_class(self):
        """
        Returns the :doc:`provider <providers>` class specified in the :doc:`config`.
        
        :returns:
            :class:`authomatic.providers.BaseProvider` subclass.
        """
        
        return resolve_provider_class(self.provider_type)
    
    
    def serialize(self):
        """
        Converts the credentials to a possibly minimal :class:`tuple` and serializes it
        to a percent encoded :class:`string` to be stored for later use.
        
        :returns:
            :class:`string`
        """
        
        # Short_name must be the first item in the tuple by all providers.
        short_name = self.provider_short_name
        # It always must be present!
        if short_name is None:
            raise exceptions.ConfigError('The provider config must have a "short_name" key set to a unique value to be able to serialize credentials!')
        
        # Get the other items for the tuple.
        rest = self.get_provider_class().to_tuple(self)
        
        # Put it together.
        result = (short_name, ) + rest
        
        # Pickle it and percent encode.
        return urllib.quote(pickle.dumps(result), '')
    
    
    @classmethod
    def deserialize(cls, config, serialized):
        """
        A *class method* which reconstructs credentials created by :meth:`serialize`.
        
        :param dict config:
            The same :doc:`config` used in the :func:`.login` to get the credentials.
        :param str serialized:
            :class:`string` The serialized credentials.
        
        :returns:
            :class:`.Credentials`
        """
        
        # Percent decode and npickle
        deserialized = pickle.loads(urllib.unquote(serialized))
        
        try:
            # We need the short name to move forward.
            short_name = deserialized[0]
            
            # Get provider config by short name.
            provider_name = short_name_to_name(config, short_name)
            cfg = config.get(provider_name)
            
            # Get the provider class.
            ProviderClass = resolve_provider_class(cfg.get('class_'))
            
            # Deserialization is provider specific.
            credentials = ProviderClass.reconstruct(deserialized, cfg)
            
            credentials.provider_name = provider_name
            
            return credentials
                        
        except (TypeError, IndexError) as e:
            raise exceptions.CredentialsError('Deserialization failed! Error: {}'.format(e))


class LoginResult(ReprMixin):
    """
    Result of the :func:`authomatic.login` function.
    """
    
    def __init__(self, provider, error=None):
        #: A :doc:`provider <providers>` instance.
        self.provider = provider
        #: An instance of the :exc:`authomatic.exceptions.BaseError` subclass.
        self.error = error
        #: A :class:`.User` instance.
        self.user = provider.user


def json_qs_parser(body):
    """
    Parses response body from json or query string.
    
    :param body: string
    """
    try:
        # try json first
        return json.loads(body)
    except ValueError:
        # then query string
        return dict(urlparse.parse_qsl(body))


class Response(ReprMixin):
    """
    Response object returned by :func:`authomatic.fetch`,
    :meth:`.Request.get_response` or :meth:`authomatic.adapters.RPC.get_response`.
    """
    
    def __init__(self, status_code, headers, content, content_parser=None):
        #: :class:`callable` A callable that takes the :attr:`content` as argument,
        #: parses it and returns the parsed data as :class:`dict`.
        self.content_parser = content_parser or json_qs_parser
        #: :class:`int` HTTP status code of the response.
        self.status_code = status_code
        #: :class:`dict` HTTP headers of the response.
        self.headers = headers
        #: :class:`str` The response body
        self.content = content
        self._data = None
    
    #TODO: Convert to method
    @property
    def data(self):
        """
        Parses the :attr:`content` with :attr:`content_parser`.
        
        :returns:
            :class:`dict`
        """
        
        if not self._data:
            self._data = self.content_parser(self.content)
        return self._data


class UserInfoResponse(ReprMixin):
    """
    A wrapper around :class:`.Response` which adds the :attr:`user` property.
    Returned by :meth:`authomatic.providers.AuthorisationProvider.fetch_user_info`.
    """
    
    def __init__(self, response, user):
        self.response = response
        self.status_code = response.status_code
        self.headers = response.headers
        self.content = response.content
        self.data = response.data
        #: A :class:`.User` instance.
        self.user = user


class Request(ReprMixin):
    """
    Abstraction of asynchronous request to **user's protected resources**.
    
    .. warning:: |async|
        
    """
    
    _repr_ignore = ('rpc',)
    
    def __init__(self, adapter, config, credentials, url, method='GET',
                 response_parser=None, content_parser=None):
        """
        Initializes the request.
        
        :param adapter:
            :doc:`Adapter <adapters>`
        :param config:
            The same :doc:`config` used in the :func:`.login` function to get the credentials.
        :param credentials:
            :class:`.Credentials` or :meth:`serialized credentials <.Credentials.serialize>`
            of the **user** whose **protected resource** we want to access.
        :param str url:
            The URL of the protected resource. Can contain query parameters.
        :param str method:
            HTTP method of the request.
        :param callable response_parser:
            A callable that takes the platform specific ``fetch`` response object
            as argument and converts it to a :class:`.Response` instance.
        :param callable content_parser:
            A callable as described in :attr:`.Response.content_parser`.
        """
        
        self.adapter = adapter
        self.url = url    
        self.method = method
        self.response_parser = response_parser
        self.content_parser = content_parser
        self.rpc = None
        
        if type(credentials) == Credentials:
            self.credentials = credentials
        elif type(credentials) == str:
            self.credentials = Credentials.deserialize(config, credentials)
    
    def fetch(self):
        """
        Fetches the protected resource and returns immediately.
        
        :returns:
            :attr:`self`
        """
        
        ProviderClass = self.credentials.get_provider_class()
        
        self.rpc = ProviderClass.fetch_async(adapter=self.adapter,
                                                          url=self.url,
                                                          credentials=self.credentials,
                                                          content_parser=self.content_parser,
                                                          method=self.method,
                                                          response_parser=self.response_parser)
        
        return self
    
    def get_response(self):
        """
        Waits for the result of :meth:`.fetch` and returns :class:`.Response`.
        
        :returns:
            :class:`.Response`
        """
        return self.rpc.get_response()


def async_fetch(adapter, config, credentials, url, method='GET', content_parser=None):
    """
    Fetches protected resource asynchronously.
       
    .. warning::
        
        |async|
    
    :param adapter:
            :doc:`Adapter <adapters>`
    :param config:
            The same :doc:`config` used in the :func:`.login` function to get the credentials.
    :param credentials:
        :class:`.Credentials` or :meth:`serialized credentials <.Credentials.serialize>`
        of the **user** whose **protected resource** we want to access.
    :param url:
        :class:`str` The URL of the protected resource.
        Can contain query parameters.
    :param method:
        :class:`str` HTTP method of the request.
    :param content_parser:
        A :class:`callable` as described in :attr:`.Response.content_parser`.
    
    :returns:
        :class:`.Request`
    """
    return Request(adapter, config, credentials, url, method, content_parser).fetch()


def fetch(adapter, config, credentials, url, method='GET', content_parser=None):
    """
    Fetches protected resource.
    
    .. note::
        
        Internally it's just a wrapper of
        ``authomatic.async_fetch(adapter, url, credentials, method, content_parser).get_response()``.
    
    :param adapter:
            :doc:`Adapter <adapters>`
    :param config:
            The same :doc:`config` used in the :func:`.login` function to get the credentials.
    :param credentials:
        :class:`.Credentials` or :meth:`serialized credentials <.Credentials.serialize>`
        of the **user** whose **protected resource** we want to access.
    :param url:
        :class:`str` The URL of the protected resource.
        Can contain query parameters.
    :param method:
        :class:`str` HTTP method of the request.
    :param content_parser:
        A :class:`callable` as described in :attr:`.Response.content_parser`.
    
    :returns:
        :class:`.Response`
    """
    return async_fetch(adapter, config, credentials, url, method, content_parser).get_response()








