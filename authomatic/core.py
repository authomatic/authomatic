#TODO: Add coding line to all modules
# -*- coding: utf-8 -*-
from urllib import urlencode
import Cookie
import base64
import binascii
import collections
import datetime
import exceptions
import hashlib
import hmac
import httplib
import logging
import pickle
import providers
import random
import sys
import time
import urllib
import urllib2
import urlparse
import webob
import settings

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

# Global variable that holds the middleware
middleware = None

# Globall variable that holds the logger
_logger = logging.getLogger(__name__)

def normalize_dict(dict_):
    """
    Replaces all values that are single-item iterables with the value of its index 0.
    
    :param dict dict_:
        Dictionary to normalize.
    
    :returns:
        Normalized dictionary.
    """
    return {k: v[0] if not type(v) is str and len(v) == 1 else v for k, v in dict_.items()}


def items_to_dict(items):
    """
    Converts list of tuples to dictionary with duplicate keys converted to lists.
    
    :param list items:
        List of tuples.
    
    :returns:
        :class:`dict`
    """
    
    res = collections.defaultdict(list)
    
    for k, v in items:
        res[k].append(v)
        
    return normalize_dict(dict(res))


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


class Session(object):
    
    def __init__(self, secret, key='authomatic', max_age=600):
        self.key = key
        self.secret = secret
        self.max_age = max_age
        self.data = self._get_data() or {}
    
    
    def _get_data(self):
        morsel = Cookie.SimpleCookie(middleware.environ.get('HTTP_COOKIE')).get(self.key)
        if morsel:
            return self._deserialize(morsel.value)
    
    
    def _signature(self, *parts):
        signature = hmac.new(self.secret, digestmod=hashlib.sha1)
        signature.update('|'.join(parts))
        return signature.hexdigest()
    
    
    def _serialize(self, value):
        """
        Converts the value to a signed string with timestamp.
        
        TODO: Check licence!
        Taken from `webapp2_extras.securecookie <http://webapp-improved.appspot.com/guide/extras.html>`_.
        
        :param value:
            Object to be serialized.
        
        :returns:
            Serialized value.
        """
        
        # 1. Serialize
        serialized = pickle.dumps(value)
        
        # 2. Encode
        encoded = base64.urlsafe_b64encode(serialized)
        
        # Create timestamp
        timestamp = str(int(time.time()))
        
        # Create signature
        signature = self._signature(self.key, encoded, timestamp)
        
        # 3. Concatenate
        return '|'.join([encoded, timestamp, signature])
    
    
    def _deserialize(self, value):
        """
        Deserializes and verifies the value created by :meth:`._serialize`.
        
        :param str value:
            The serialized value.
        
        :returns:
            Desrialized object.
        """
        
        # 3. Split
        encoded, timestamp, signature = value.split('|')
        
        # Verify signature
        if not signature == self._signature(self.key, encoded, timestamp):
            return None
        
        # Verify timestamp
        if int(timestamp) < int(time.time()) - self.max_age:
            return None
        
        # 2. Decode
        decoded = base64.urlsafe_b64decode(encoded)
        
        # 1. Deserialize
        deserialized = pickle.loads(decoded)
        
        return deserialized
    
    
    def __setitem__(self, key, value):
        self.data[key] = value
        
        middleware.set_header('Set-Cookie', '{}={}'.format(self.key, self._serialize(self.data)))
    
    
    def __getitem__(self, key):
        return self.data.__getitem__(key)
    
    
    def __delitem__(self, key):
        return self.data.__delitem__(key)
    
    
    def get(self, key, default=None):
        return self.data.get(key, default)


def call_wsgi(app, environ):
    
    sh = [None, None]
    
    def start_response(status, headers):
        sh[:] = [status, headers]
    
    app_iter = app(environ, start_response)
    
    status, headers = sh
    
    return app_iter, status, headers


class Middleware(object):
    
    def __init__(self, app, config, session=None,
                 report_errors=True, logging_level=logging.DEBUG,
                 prefix='authomatic'):
        self.app = app
        self.session = session
        self.pending = False
        
        # Set global settings.
        settings.config = config
        settings.report_errors = report_errors
        settings.prefix = prefix
        settings.logging_level = logging_level
        
        # Set logging level.
        _logger.setLevel(logging_level)
    
    def __call__(self, environ, start_response):
        global config
        
        self._post = {}
        self._get = {}
        self.output = []
        self.status = '200 OK'
        self.headers = []
        self.environ = environ
        self.session = self.session or Session('abcdefg')
        
        
        app_output, app_status, app_headers = call_wsgi(self.app, environ)
#        app_output = self.app(environ, start_response)
        
        
#        if self.output or self.headers:
        if self.pending:
            start_response(self.status, self.headers, sys.exc_info())
            return self.output
        else:
            start_response(app_status, app_headers, sys.exc_info())
            return app_output
    
    
    @property
    def url(self):
        scheme = self.environ.get('wsgi.url_scheme')
        host = self.environ.get('HTTP_HOST')
        path = self.environ.get('PATH_INFO')
        return urlparse.urlunsplit((scheme, host, path, 0, 0))
    
    
    @property
    def body(self):
        length = int(self.environ.get('CONTENT_LENGTH', '0'))
        
        if length:
            body = self.environ.get('wsgi.input').read(length)
            return body
        else:
            return ''
    
    
    def _to_dict(self, items):
        return {k: v[0] if len(v) == 1 else v for k, v in items}
    
    
    def _parse_qs(self, qs):
        qs = urlparse.parse_qs(qs)
        return self._to_dict(qs.items())
    
    
    @property
    def post(self):
        if self._post:
            return self._post
        else:
            self._post = self._parse_qs(self.body)
            return self._post
    
    
    @property
    def get(self):
        if self._get:
            return self._get
        else:
            self._get = self._parse_qs(self.environ.get('QUERY_STRING'))
            return self._get
    
    
    @property
    def params(self):
        res = {}
        
        # Normalize common values of GET and POST to one key with list value.
        for k, v in self.get.items():
            if k in self.post:
                vp = self.post[k]
                vp = vp if type(vp) is list else [vp]
                vg = v if type(v) is list else [v]                
                res[k] = vg + vp
            else:
                res[k] = v
        return res
    
    
    def set_header(self, key, value):
        self.headers.append((key, value))
    
    
    def write(self, value):
        self.output.append(value)
    
    
    def redirect(self, url):
        self.status = '302 Found'
        self.set_header('Location', url)


def setup_middleware(*args, **kwargs):
    global middleware
    middleware = Middleware(*args, **kwargs)
    return middleware


def login(provider_name, callback=None, **kwargs):
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
        The main login procedure events have level ``INFO``, others like adapter database access_with_credentials
        have level ``DEBUG``.
        
    .. note::
        
        Accepts other :doc:`provider <providers>` specific keyword arguments.
    
    :returns:
        :obj:`None` or :class:`.LoginResult`.
    """
    
    # TODO: Move report_errors and logging to Middleware
    
    # retrieve required settings for current provider and raise exceptions if missing
    provider_settings = settings.config.get(provider_name)
    if not provider_settings:
        raise exceptions.ConfigError('Provider name "{}" not specified!'.format(provider_name))
    
    class_ = provider_settings.get('class_')
    if not class_:
        raise exceptions.ConfigError('The "class_" key not specified in the config for provider {}!'.format(provider_name))
    
    ProviderClass = resolve_provider_class(class_)
    
    # instantiate provider class
    provider = ProviderClass(provider_name, callback, **kwargs)
    
    middleware.pending = True
    
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
    
    _repr_sensitive = ('token', 'refresh_token', 'token_secret', 'consumer_key', 'consumer_secret')
    
    def __init__(self, **kwargs):
        
        #: :class:`str` User **access_with_credentials token**.
        self.token = kwargs.get('token')
        
        #: :class:`str` User **access_with_credentials token**.
        self.refresh_token = kwargs.get('refresh_token')
        
        #: :class:`str` User **access_with_credentials token secret**.
        self.token_secret = kwargs.get('token_secret')
        
        #: :class:`datetime.datetime()` Expiration date of the **access_with_credentials token**.
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
            
            #: :class:`class` Provider class.
            self.provider_class = provider.__class__
            
            #: :class:`str` Consumer key specified in the :doc:`config`.
            self.consumer_key = provider.consumer_key
            
            #: :class:`str` Consumer secret specified in the :doc:`config`.
            self.consumer_secret = provider.consumer_secret
            
        else:
            self.provider_name = kwargs.get('provider_name')
            self.provider_type = kwargs.get('provider_type')
            self.provider_short_name = kwargs.get('provider_short_name')
            self.provider_class = kwargs.get('provider_class')
            
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
    
    
    def refresh(self):
        if hasattr(self.provider_class, 'refresh_credentials'):
            return self.provider_class.refresh_credentials(self)
    
    
    def provider_type_class(self):
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
        rest = self.provider_type_class().to_tuple(self)
        
        # Put it together.
        result = (short_name, ) + rest
        
        # Pickle it and percent encode.
        # TODO: encode to base64
        return urllib.quote(pickle.dumps(result), '')
    
    
    @classmethod
    def deserialize(cls, credentials):
        """
        A *class method* which reconstructs credentials created by :meth:`serialize`.
        
        :param dict config:
            The same :doc:`config` used in the :func:`.login` to get the credentials.
        :param str credentials:
            :class:`string` The serialized credentials.
        
        :returns:
            :class:`.Credentials`
        """
        
        # Accept both serialized and normal.
        if type(credentials) is Credentials:
            return credentials
        
        # Percent decode and pickle
        # TODO: decode from base64
        unpickled = pickle.loads(urllib.unquote(credentials))
        
        try:
            # We need the short name to move forward.
            short_name = unpickled[0]
            
            # Get provider config by short name.
            provider_name = short_name_to_name(settings.config, short_name)
            cfg = settings.config.get(provider_name)
            
            # Get the provider class.
            ProviderClass = resolve_provider_class(cfg.get('class_'))
            
            # Deserialization is provider specific.
            deserialized = ProviderClass.reconstruct(unpickled, cfg)
            
            deserialized.provider_name = provider_name
            deserialized.provider_class = ProviderClass
            
            return deserialized
                        
        except (TypeError, IndexError) as e:
            raise exceptions.CredentialsError('Deserialization failed! Error: {}'.format(e))


def credentials(credentials):
    """
    Deserializes credentials if needed.
    
    :param credentials:
        Credentials serialized with :meth:`.Credentials.serialize` or :class:`.Credentials` instance.
    
    :returns:
        :class:`.Credentials`
    """
    return Credentials.deserialize(credentials)


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
    Wraps :class:`httplib.HTTPResponse` and adds
    :attr:`.content` and :attr:`.data` attributes.
    """
    
    def __init__(self, httplib_response, content_parser=None):
        """
        :param httplib_response:
            The wrapped :class:`httplib.HTTPResponse` instance.
            
        :param function content_parser:
            Callable which accepts :attr:`.content` as argument,
            parses it and returns the parsed data as :class:`dict`.
        """
        
        self.httplib_response = httplib_response
        self.content_parser = content_parser or json_qs_parser
        self._data = None
        self._content = None
        
        #: Same as :attr:`httplib.HTTPResponse.msg`.
        self.msg = httplib_response.msg        
        #: Same as :attr:`httplib.HTTPResponse.version`.
        self.version = httplib_response.version        
        #: Same as :attr:`httplib.HTTPResponse.status`.
        self.status = httplib_response.status        
        #: Same as :attr:`httplib.HTTPResponse.reason`.
        self.reason = httplib_response.reason
    
    
    def read(self, amt=None):
        """
        Same as :meth:`httplib.HTTPResponse.read`.
        
        :param amt:
        """
    
        return self.httplib_response.read(amt)
    
    
    def getheader(self, name, default=None):
        """
        Same as :meth:`httplib.HTTPResponse.getheader`.
        
        :param name:
        :param default:
        """
        
        return self.httplib_response.getheader(name, default)
    
    
    def fileno(self):
        """
        Same as :meth:`httplib.HTTPResponse.fileno`.
        """
        return self.httplib_response.fileno()
    
    
    def getheaders(self):
        """
        Same as :meth:`httplib.HTTPResponse.getheaders`.
        """
        return self.httplib_response.getheaders()
    
    
    @property
    def content(self):
        """
        The whole response content.
        """
        
        if not self._content:
            self._content = self.httplib_response.read()
        return self._content
    
    
    @property
    def data(self):
        """
        A :class:`dict` of data parsed from :attr:`.content`.
        """
        
        if not self._data:
            self._data = self.content_parser(self.content)
        return self._data


class UserInfoResponse(Response):
    """
    Inherits from :class:`.Response`, adds  :attr:`.user` attribute.
    """
    
    def __init__(self, user, *args, **kwargs):
        super(UserInfoResponse, self).__init__(*args, **kwargs)
        
        #: :class:`.User` instance.
        self.user = user

def access(credentials, url, method='GET', headers={}, max_redirects=5, content_parser=None):
    """
    
    
    :param credentials:
    :param url:
    :param method:
    :param headers:
    :param content_parser:
    """
    
    # Deserialize credentials.
    credentials = Credentials.deserialize(credentials)
    
    # Resolve provider class.
    ProviderClass = credentials.provider_class
    
    # Access resource and return response.
    return ProviderClass.access_with_credentials(credentials, url, method,
                                                 headers, max_redirects, content_parser)
    
    







