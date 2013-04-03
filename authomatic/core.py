# -*- coding: utf-8 -*-
from authomatic.exceptions import SessionError, MiddlewareError
import Cookie
import collections
import copy
import datetime
import exceptions
import hashlib
import hmac
import logging
import pickle
import settings
import sys
import threading
import time
import urllib
import urlparse
from xml.etree import ElementTree

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

#===============================================================================
# Global variables
#===============================================================================

middleware = None
_logger = logging.getLogger(__name__)
_counter = None


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


class Counter(object):
    """
    A simple counter to be used in the config to generate unique `id` values.
    """
    
    def __init__(self, start=0):
        self._count = start
        
    def count(self):
        self._count += 1
        return self._count

_counter = Counter()

def provider_id():
    """
    A simple counter to be used in the config to generate unique `IDs`.
    
    :returns:
        :class:`int`.
     
    Use it in the :doc:`config` like this:
    ::
    
        import authomatic
        
        CONFIG = {
            'facebook': {
                 'class_': authomatic.providers.oauth2.Facebook,
                 'id': authomatic.provider_id(), # returns 1
                 'consumer_key': '##########',
                 'consumer_secret': '##########',
                 'scope': ['user_about_me', 'email']
            },
            'google': {
                 'class_': 'authomatic.providers.oauth2.Google',
                 'id': authomatic.provider_id(), # returns 2
                 'consumer_key': '##########',
                 'consumer_secret': '##########',
                 'scope': ['https://www.googleapis.com/auth/userinfo.profile',
                           'https://www.googleapis.com/auth/userinfo.email']
            },
            'windows_live': {
                 'class_': 'oauth2.WindowsLive',
                 'id': authomatic.provider_id(), # returns 3
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


def json_qs_parser(body):
    """
    Parses response body from JSON, XML or query string.
    
    :param body:
        string
    
    :returns:
        :class:`dict`, :class:`list` if input is JSON or query string,
        :class:`xml.etree.ElementTree.Element` if XML.
    """
    
    try:
        # Try JSON first.
        logging.info('JSON')
        return json.loads(body)
    except:
        pass
    
    try:
        # Then XML.
        logging.info('XML')
        return ElementTree.fromstring(body)
    except:
        pass
    
    # Finally query string.
    logging.info('QS')
    return dict(urlparse.parse_qsl(body))


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


def id_to_name(config, short_name):
    """
    Returns the provider :doc:`config` key based on it's
    ``id`` value.
    
    :param dict config:
        :doc:`config`.
    :param id:
        Value of the id parameter in the :ref:`config` to search for.
    """
    
    for k, v in config.items():
        if v.get('id') == short_name:
            return k
            break
    else:
        raise Exception('No provider with id={} found in the config!'.format(short_name))


def call_wsgi(app, environ):
    """
    Calls a WSGI application.
    
    :param app:
        WSGI application.
        
    :param dict environ:
        The WSGI *environ* dictionary.
    """
    
    # Placeholder for status, headers and exec_info.
    args = [None, None]
    
    def start_response(status, headers, exc_info=None):
        """
        Dummy start_response to retrieve status, headersand  exc_info from the app.
        """
        # Copy values.
        args[:] = [status, headers, exc_info]
    
    # Call the WSGI app and pass it our start_response.
    app_iter = app(environ, start_response)
    
    # Unpack values
    status, headers, exc_info = args
    
    return app_iter, status, headers, exc_info


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


class Future(threading.Thread):
    """
    Represents an activity run in a separate thread.
    Subclasses the standard library :class:`threading.Thread` and adds :attr:`.get_result` method.
    
    .. warning:: |async|
    
    """
    
    def __init__(self, func, *args, **kwargs):
        """
        :param callable func:
            The function to be run in separate thread.
        
        Calls :data:`func` in separate thread and returns immediately.
        Accepts arbitrary positional and keyword arguments which will be passed to :data:`func`.
        """
        
        super(Future, self).__init__()
        self._func = func
        self._args = args
        self._kwargs = kwargs
        self._result = None
        
        self.start()
    
    
    def run(self):
        self._result = self._func(*self._args, **self._kwargs)
    
    
    def get_result(self, timeout=None):
        """
        Waits for the wrapped :data:`func` to finish and returns its result.
        
        .. note::
            
            This will block the **calling thread** until the :data:`func` returns.
        
        :param timeout:
            :class:`float` or ``None`` A timeout for the :data:`func` to return in seconds.
        
        :returns:
            The result of the wrapped :data:`func`.
        """
        
        self.join(timeout)
        return self._result


class Session(object):
    """
    A dictionary-like secure cookie session implementation.
    """
    
    # List of keys which values are not json serializable.
    NOT_JSON_SERIALIZABLE = ['_yadis_services__openid_consumer_',
                             '_openid_consumer_last_token']
    
    def __init__(self, secret, name='authomatic', max_age=600, secure=False):
        """
        :param str secret:
            Session secret used to sign the session cookie.
        :param str name:
            Session cookie name.
        :param int max_age:
            Maximum allowed age of session kookie nonce in seconds.
        :param bool secure:
            If ``True`` the session cookie will be saved wit ``Secure`` attribute.
        """
        
        self.name = name
        self.secret = secret
        self.max_age = max_age
        self.secure = secure
        
        self._data = {}
    
    
    def create_cookie(self, delete=None):
        """
        Creates the value for ``Set-Cookie`` HTTP header.
        
        :param bool delete:
            If ``True`` the cookie value will be ``deleted`` and the
            Expires value will be ``Thu, 01-Jan-1970 00:00:01 GMT``.
        """
        
        template = '{name}={value}; Domain={domain}; Path={path}; HttpOnly{secure}{expires}'
        
        value = 'deleted' if delete else self._serialize(self.data)
        
        return template.format(name=self.name,
                               value=value,
                               domain=middleware.domain,
                               path=middleware.path,
                               secure='; Secure' if self.secure else '',
                               expires='; Expires=Thu, 01-Jan-1970 00:00:01 GMT' if delete else '')
    
    
    def save(self):
        """
        Adds the session cookie to headers.
        """
        if self.data:
            # Set the cookie header.
            middleware.set_header('Set-Cookie', self.create_cookie())
            
            # Reset data
            self._data = {}
    
    
    def _get_data(self):
        """
        Extracts the session data from cookie.
        """
        
        morsel = Cookie.SimpleCookie(middleware.environ.get('HTTP_COOKIE')).get(self.name)
        if morsel:
            return self._deserialize(morsel.value)
        else:
            return {}
    
    
    @property
    def data(self):
        """
        Gets session data lazily.
        """
        
        if not self._data:
            self._data = self._get_data()
        return self._data
        
    
    def _signature(self, *parts):
        """
        Creates signature for the session.
        """
        
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
        
        data = copy.deepcopy(value)
        
        # 1. Handle non json serializable objects.
        for key in self.NOT_JSON_SERIALIZABLE:
            if key in data.keys():
                data[key] = pickle.dumps(data[key])
        
        
        # 2. Serialize
        serialized = json.dumps(data)
        
        # 3. Encode
        # Percent encoding produces smaller result then urlsafe base64.
        encoded = urllib.quote(serialized, '')
        
        # Create timestamp
        timestamp = str(int(time.time()))
        
        # Create signature
        signature = self._signature(self.name, encoded, timestamp)
        
        # 4. Concatenate
        return '|'.join([encoded, timestamp, signature])
    
    
    def _deserialize(self, value):
        """
        Deserializes and verifies the value created by :meth:`._serialize`.
        
        :param str value:
            The serialized value.
        
        :returns:
            Desrialized object.
        """
        
        # 4. Split
        encoded, timestamp, signature = value.split('|')
        
        # Verify signature
        if not signature == self._signature(self.name, encoded, timestamp):
            raise SessionError('Invalid signature "{}"!'.format(signature))
        
        # Verify timestamp
        if int(timestamp) < int(time.time()) - self.max_age:
            return None
        
        # 3. Decode
        decoded = urllib.unquote(encoded)
        
        # 2. Deserialize
        deserialized = json.loads(decoded)
        
        # 1. Unpicke non json serializable objects.
        for key in self.NOT_JSON_SERIALIZABLE:
            if key in deserialized.keys():
                deserialized[key] = pickle.loads(deserialized[key])
        
        return deserialized
    
    
    def __setitem__(self, key, value):
        self._data[key] = value
    
    
    def __getitem__(self, key):
        return self.data.__getitem__(key)
    
    
    def __delitem__(self, key):
        return self._data.__delitem__(key)
    
    
    def get(self, key, default=None):
        return self.data.get(key, default)


class Middleware(object):
    """
    WSGI middleware responsible for these task during the **login procedure**:
    
    
        * Introspection of current request.
        * Response creation.
        * Session management.
    
    """
    
    def __init__(self, app, config, secret, session_max_age=600, secure_cookie=False,
                 session=None, session_save_method=None, report_errors=True, debug=False,
                 logging_level=logging.INFO, prefix='authomatic',
                 fetch_headers={}):
        """
        :param app:
            WSGI application that should be wrapped.
            
        :param dict config:
            :doc:`config`
            
        :param str secret:
            A secret string that will be used as the key for signing :class:`.Session` cookie and
            as a salt by *CSRF* token generation.
            
        :param session_max_age:
            Maximum allowed age of :class:`.Session` kookie nonce in seconds.
            
        :param bool secure_cookie:
            If ``True`` the :class:`.Session` cookie will be saved wit ``Secure`` attribute.
        
        :param session:
            Custom dictionary-like session implementation.
        
        :param callable session_save_method:
            A method of the supplied session or any mechanism that saves the session data and cookie.
        
        :param bool report_errors:
            If ``True`` exceptions encountered during the **login procedure**
            will be caught and reported in the :attr:`.LoginResult.error` attribute.
            Default is ``True``.
        
        :param bool debug:
            If ``True`` traceback of exceptions will be written to response.
            Default is ``False``.
            
        :param int logging_level:
            The logging level treshold as specified in the standard Python
            `logging library <http://docs.python.org/2/library/logging.html>`_.
            Default is ``logging.INFO``
        
        :param str prefix:
            Prefix used as the :class:`.Session` cookie name and
            by which all logs will be prefixed.
        """
        
        self.app = app
        self.pending = False
        
        # Set global settings.
        settings.config = config
        settings.secret = secret
        settings.report_errors = report_errors
        settings.debug = debug
        settings.prefix = prefix
        settings.secure_cookie = secure_cookie
        settings.session_max_age = session_max_age
        settings.logging_level = logging_level
        settings.fetch_headers = fetch_headers
        
        self.set_session(session, session_save_method)
        
        
        # Set logging level.
        _logger.setLevel(logging_level)
    
    
    def __call__(self, environ, start_response):
        """
        The WSGI mechanism.
        
        :param environ:
        :param start_response:
        """
        
        global config
        
        # Set request specific properties.
        self._post = {}
        self._get = {}
        self.output = []
        self.status = '200 OK'
        self.headers = []
        self.environ = environ
        
        self.scheme = self.environ.get('wsgi.url_scheme')
        self.host = self.environ.get('HTTP_HOST')
        self.domain = self.host.split(':')[0]
        self.path = self.environ.get('PATH_INFO')
        self.url = urlparse.urlunsplit((self.scheme, self.host, self.path, 0, 0))
        
        # Call the wrapped WSGI app and store it's output for later.
        app_output, app_status, app_headers, exc_info = call_wsgi(self.app, environ)
        
        if self.pending:
            # This middleware intercepts only if the login procedure is pending.
            if not isinstance(self.session, Session):
                # We must use the "Set-Cookie" header of the wrapped app
                # if custom session was specified.
                cookie_value = dict(app_headers).get('Set-Cookie', '')
                session_header = ('Set-Cookie', cookie_value)
                self.headers.append(session_header)
            
            start_response(self.status, self.headers, sys.exc_info())
            return self.output
        else:
            # If login procedure has finished.
            if isinstance(self.session, Session):
                # If default session is used, delete our session cookie.
                app_headers.append(('Set-Cookie', self.session.create_cookie(delete=True)))
            
            # Write out the output of the wrapped WSGI app.
            start_response(app_status, app_headers, sys.exc_info())
            
            return app_output
    
    
    def set_session(self, session, session_save_method):
        """
        Allows for a custom dictionary-like session to be used.
        The session must implement the :class:`.extras.interfaces.BaseSession` interface.
        
        :param dict session:
            A dictionary-like session instance.
            
        :param callable session_save_method:
            A callable that saves the session data and sets the session cookie to response.
        """
        
        if session is None:
            # Use default session.
            self.session = Session(settings.secret,
                                   max_age=settings.session_max_age,
                                   name=settings.prefix,
                                   secure=settings.secure_cookie)
            
            self.save_session = self.session.save
        else:
            # Use custom session.
            if session_save_method is None:
                raise MiddlewareError('If you want to use custom "session", you must also ' + \
                                      'specify with the "session_save_method" argument!')
            else:
                self.session = session
                self.save_session = session_save_method
        
    
    
    @property
    def body(self):
        """
        The HTTP request body.
        """
        
        length = int(self.environ.get('CONTENT_LENGTH', '0'))
        
        if length:
            body = self.environ.get('wsgi.input').read(length)
            return body
        else:
            return ''
    
    
    def _clean_dict(self, items):
        """
        Converts all single-item values to its index [0] value.
        
        :param list items:
            List of tuples.
        
        :returns:
            :class:`dict`
        """
        
        return {k: v[0] if len(v) == 1 else v for k, v in items}
    
    
    def _parse_qs(self, qs):
        """
        Parses query string and returns cleaned dictionary.
        
        :param str qs:
            Query string.
        
        :returns:
            :class:`dict`
        """
        
        qs = urlparse.parse_qs(qs)
        return self._clean_dict(qs.items())
    
    
    @property
    def post(self):
        """
        Returns parsed POST parameters.
        
        :returns:
            :class:`dict`
        """
        
        if self._post:
            return self._post
        else:
            self._post = self._parse_qs(self.body)
            return self._post
    
    
    @property
    def get(self):
        """
        Returns parsed GET parameters.
        
        :returns:
            :class:`dict`
        """
        
        if self._get:
            return self._get
        else:
            self._get = self._parse_qs(self.environ.get('QUERY_STRING'))
            return self._get
    
    
    @property
    def params(self):
        """
        Returns combined GET and POST parameters.
        
        :returns:
            :class:`dict`
        """
        
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
        """
        Appends a HTTP response header.
        
        :param str key:
            The name of the header.
        
        :param str value:
            The header value.
        """
        
        self.headers.append((key, value))
    
    
    def write(self, value):
        """
        Writes the value to HTTP response
        
        :param str value:
            The string to be written to response.
        """
        self.output.append(value)
    
    
    def redirect(self, location):
        """
        Writes a ``302 Found`` redirect to specified location.
        
        :param str location:
            The URL to redirect to.
        """
        
        self.status = '302 Found'
        self.set_header('Location', location)


class User(ReprMixin):
    """
    Provides unified interface to selected **user** info returned by different **providers**.
    
    .. note:: The value format may vary across providers.
    """
    
    def __init__(self, provider, **kwargs):
        #: A :doc:`provider <providers>` instance.
        self.provider = provider
        
        #: An :class:`.Credentials` instance.
        self.credentials = kwargs.get('credentials')
        
        #: A :class:`dict` containing all the **user** information returned by the **provider**.
        #: The structure differs across **providers**.
        self.data = kwargs.get('data')
        
        #: The :attr:`.Response.content` of the request made to update the user.
        self.content = kwargs.get('content')
        
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
        #: :class:`str` phone.
        self.phone = kwargs.get('phone')
        #: :class:`str` Picture URL.
        self.picture = kwargs.get('picture')
        #: Birth date as :class:`datetime.datetime()` or :class:`str` if parsing failed or ``None``.
        self.birth_date = kwargs.get('birth_date')
        #: :class:`str` Country.
        self.country = kwargs.get('country')
        #: :class:`str` City.
        self.city = kwargs.get('city')
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
    
    
    def async_update(self):
        """
        Same as :meth:`.update` but runs asynchronously in a separate thread.
        
        .. warning:: |async|
        
        :returns:
            :class:`.Future` instance representing the separate thread.
        """
        
        return Future(self.update)


class Credentials(ReprMixin):
    """Contains all neccessary informations to fetch **user's protected resources**."""
    
    _repr_sensitive = ('token', 'refresh_token', 'token_secret', 'consumer_key', 'consumer_secret')
    
    def __init__(self, **kwargs):
        
        #: :class:`str` User **access token**.
        self.token = kwargs.get('token', '')
        
        #: :class:`str` Access token type.
        self.token_type = kwargs.get('token_type', '')
        
        #: :class:`str` Refresh token.
        self.refresh_token = kwargs.get('refresh_token', '')
        
        #: :class:`str` Access token secret.
        self.token_secret = kwargs.get('token_secret', '')
        
        #: :class:`int` Expiration date as UNIX timestamp.
        self.expiration_time = int(kwargs.get('expiration_time', 0))
        
        #: A :doc:`Provider <providers>` instance**.
        provider = kwargs.get('provider')
        
        self.expire_in = int(kwargs.get('expire_in', 0))
        
        if provider:
            #: :class:`str` Provider name specified in the :doc:`config`.
            self.provider_name = provider.name
            
            #: :class:`str` Provider type e.g. ``"authomatic.providers.oauth2.OAuth2"``.
            self.provider_type = provider.get_type()
            
            #: :class:`str` Provider short name specified in the :doc:`config`.
            self.provider_id = int(provider.id)            
            
            #: :class:`class` Provider class.
            self.provider_class = provider.__class__
            
            #: :class:`str` Consumer key specified in the :doc:`config`.
            self.consumer_key = provider.consumer_key
            
            #: :class:`str` Consumer secret specified in the :doc:`config`.
            self.consumer_secret = provider.consumer_secret
            
        else:
            self.provider_name = kwargs.get('provider_name', '')
            self.provider_type = kwargs.get('provider_type', '')
            self.provider_id = int(kwargs.get('provider_id'))
            self.provider_class = kwargs.get('provider_class')
            
            self.consumer_key = kwargs.get('consumer_key', '')
            self.consumer_secret = kwargs.get('consumer_secret', '')
    
    
    @property
    def expire_in(self):
        """
        
        """
        
        return self._expire_in
    
    @expire_in.setter
    def expire_in(self, value):
        """
        Computes :attr:`.expiration_time` when the value is set.
        """
        
        if value:
            self._expiration_time = int(time.time()) + int(value)
            self._expire_in = value
    
    
    @property
    def expiration_time(self):
        return self._expiration_time
    
    @expiration_time.setter
    def expiration_time(self, value):
        self._expiration_time = int(value)
        self._expire_in = self._expiration_time - int(time.time())
    
    
    @property
    def expiration_date(self):
        """
        Expiration date as :class:`datetime.datetime` or ``None`` if credentials never expire.
        """
        
        if self.expire_in < 0:
            return None
        else:
            return datetime.datetime.fromtimestamp(self.expiration_time)
    
    
    @property
    def valid(self):
        """
        ``True`` if credentials are valid, ``False`` if expired.
        """
        
        if self.expiration_time:
            return self.expiration_time > int(time.time())
        else:
            return True
    
    
    def expire_soon(self, seconds):
        """
        Returns ``True`` if credentials expire sooner than specified.
        
        :param int seconds:
            Number of seconds.
            
        :returns:
            ``True`` if credentials expire sooner than specified, else ``False``.
        """
        
        if self.expiration_time:
            return self.expiration_time < int(time.time()) + int(seconds)
        else:
            return False
    
    
    def refresh(self, force=False, soon=86400):
        """
        Refreshes the credentials only if the **provider** supports it and
        if it will expire in less than one day.
        It does nothing in other cases.
        
        .. note::
        
            The credentials will be refreshed only if it gives sense
            i.e. only |oauth2|_ has the notion of credentials *refreshment/extension*.
            And there are also differences across providers
            e.g. Google supports refreshment only if there is a ``refresh_token`` in the credentials and
            that in turn is present only if the ``access_type`` parameter was set to ``offline``
            in the **user authorisation request**.
        
        :param bool force:
            If ``True`` the credentials will be refreshed even if they won't expire soon.
        
        :param int soon:
            Number of seconds specifying what means *soon*.
        """
        
        if hasattr(self.provider_class, 'refresh_credentials'):
            if force or self.expire_soon(soon):
                return self.provider_class.refresh_credentials(self)
    
    
    def async_refresh(self, *args, **kwargs):
        """
        Same as :meth:`.refresh` but runs asynchronously in a separate thread.
        
        .. warning:: |async|
        
        :returns:
            :class:`.Future` instance representing the separate thread.
        """
        
        return Future(self.refresh, *args, **kwargs)
    
    
    def provider_type_class(self):
        """
        Returns the :doc:`provider <providers>` class specified in the :doc:`config`.
        
        :returns:
            :class:`authomatic.providers.BaseProvider` subclass.
        """
        
        return resolve_provider_class(self.provider_type)
    
    
    def serialize(self):
        """
        Converts the credentials to a percent encoded string to be stored for later use.
        
        :returns:
            :class:`string`
        """
        
        # Short_name must be the first item in the tuple by all providers.
        short_name = self.provider_id
        # It always must be present!
        if short_name is None:
            raise exceptions.ConfigError('The provider config must have a "id" key set to a unique value to be able to serialize credentials!')
        
        # Get the remaining items for the tuple.
        rest = self.provider_type_class().to_tuple(self)
        
        # Put it together.
        result = (short_name, ) + rest
        
        # Make sure that all items are strings.
        stringified = [str(i) for i in result]
        
        # Concatenate by newline.
        concatenated = '\n'.join(stringified)
        
        # Percent encode.
        return urllib.quote(concatenated, '')
    
    
    @classmethod
    def deserialize(cls, credentials):
        """
        A *class method* which reconstructs credentials created by :meth:`serialize`.
        You can also passit a :class:`.Credentials` instance.
        
        :param dict config:
            The same :doc:`config` used in the :func:`.login` to get the credentials.
        :param str credentials:
            :class:`string` The serialized credentials or :class:`.Credentials` instance.
        
        :returns:
            :class:`.Credentials`
        """
        
        # Accept both serialized and normal.
        if type(credentials) is Credentials:
            return credentials
        
        decoded = urllib.unquote(credentials)
        
        split = decoded.split('\n')
        
        # We need the short name to move forward.
        short_name = int(split[0])
        
        # Get provider config by short name.
        provider_name = id_to_name(settings.config, short_name)
        cfg = settings.config.get(provider_name)
        
        # Get the provider class.
        ProviderClass = resolve_provider_class(cfg.get('class_'))
        
        # Deserialization is provider specific.
        deserialized = ProviderClass.reconstruct(split, cfg)
        
        deserialized.provider_name = provider_name
        deserialized.provider_class = ProviderClass
        
        return deserialized

_JS_CALLBACK_HTML = """
<!DOCTYPE html>
<html>
<head>
<title></title>
</head>
<body>
<script type="text/javascript">
{user}
{error}
var result = {{}};
result.user = user;
result.error = error;
result.provider_name = "{provider_name}";
{custom}
window.opener.{callback}(result);
window.close();
</script>
</body>
</html>
"""

class LoginResult(ReprMixin):
    """
    Result of the :func:`authomatic.login` function.
    """
    
    def __init__(self, provider):
        #: A :doc:`provider <providers>` instance.
        self.provider = provider
        
        #: An instance of the :exc:`authomatic.exceptions.BaseError` subclass.
        self.error = None
    
    def js_callback(self, callback, **kwargs):
        """
        Returns HTML with javascript that calls the specified javascript callback
        on the opener of the login handler with a ``result`` object passed to it
        and subsequently closes itself.
        
        :param str callback:
            The name of the javascript callback.
            
        :param **kwargs:
            Additional keyword arguments will be added as properties to the javascript result object.
        
        :returns:
            HTML with javascript that calls the calback on the opener and closes itself.
        """
        
        # User
        if self.user:
            user = 'var user = {};\n'
            for k, v in self.user.__dict__.items():
                if not k in ('gae_user', 'provider', 'credentials', 'data', 'content'):
                    user += 'user.{} = "{}";\n'.format(k, v or '')
            
            user += 'user.content = {};\n'.format(self.user.content or '{}')
            user += 'user.credentials = "{}";\n'.format(self.user.credentials.serialize() if self.user.credentials else '')
        else:
            user = 'var user = null;\n'
        
        # Error
        if self.error:
            error = 'var error = {};\n'
            for k, v in self.error.__dict__.items():
                error += 'error.{} = "{}";\n'.format(k, v or '')
        else:
            error = 'var error = null;\n'
        
        # Custom properties
        custom = ''
        for k, v in kwargs.items():
            v = 'null' if v is None else v
            custom += 'result.{} = {};\n'.format(k, v)
        
        return _JS_CALLBACK_HTML.format(user=user,
                                        error=error,
                                        provider_name=self.provider.name,
                                        custom=custom,
                                        callback=callback)
    
    @property
    def user(self):
        """
        A :class:`.User` instance.
        """
        
        return self.provider.user
    
    @property
    def pending(self):
        """
        ``False`` if the *login procedure* has finished, ``True`` if still pending.
        """
        
        return middleware.pending


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


#===============================================================================
# Public methods
#===============================================================================


def setup_middleware(*args, **kwargs):
    """
    Wrapps your WSGI application in middleware which adds the **authorisation/authentication**
    capability to it.
    
    :param app:
            WSGI application to wrap.
        
    :param dict config:
        :doc:`config`
        
    :param str secret:
        A secret string that will be used as the key for signing :class:`.Session` cookie and
        as a salt by *CSRF* token generation.
        
    :param session_max_age:
        Maximum allowed age of :class:`.Session` kookie nonce in seconds.
        
    :param bool secure_cookie:
        If ``True`` the :class:`.Session` cookie will be saved wit ``Secure`` attribute.
    
    :param session:
        Custom dictionary-like session implementation.
    
    :param callable session_save_method:
        A method of the supplied session or any mechanism that saves the session data and cookie.
    
    :param bool report_errors:
        If ``True`` exceptions encountered during the **login procedure**
        will be caught and reported in the :attr:`.LoginResult.error` attribute.
        Default is ``True``.
    
    :param bool debug:
        If ``True`` traceback of exceptions will be written to response.
        Default is ``False``.
        
    :param int logging_level:
        The logging level treshold as specified in the standard Python
        `logging library <http://docs.python.org/2/library/logging.html>`_.
        Default is ``logging.INFO``
    
    :param str prefix:
        Prefix used as the :class:`.Session` cookie name and
        by which all logs will be prefixed.
    """
    
    global middleware
    middleware = Middleware(*args, **kwargs)
    return middleware


def login(provider_name, callback=None, session=None, session_save_method=None, **kwargs):
    """
    Launches a login procedure for specified :doc:`provider </reference/providers>` and returns :class:`.LoginResult`.
    
    .. warning::
        
        The function redirects the **user** to the **provider** which in turn redirects the
        **user** back to the *request handler* where this function was called.
    
    :param str provider_name:
        Name of the provider as specified in the keys of the :doc:`config`.
        
    :param callable callback:
        If specified the function will call the callback with :class:`.LoginResult`
        passed as argument and will return nothing.
        
    :param bool report_errors:
        
    .. note::
        
        Accepts additional keyword arguments that will be passed to :doc:`provider` constructor.
    
    :returns:
        :class:`.LoginResult`
    """
    
    # Handle custom session.
    middleware.set_session(session, session_save_method)
    
    # Inform middleware that the login procedure started.
    middleware.pending = True
    
    # retrieve required settings for current provider and raise exceptions if missing
    provider_settings = settings.config.get(provider_name)
    if not provider_settings:
        pass
        raise exceptions.ConfigError('Provider name "{}" not specified!'.format(provider_name))
    
    # Resolve provider class.
    class_ = provider_settings.get('class_')
    if not class_:
        raise exceptions.ConfigError('The "class_" key not specified in the config for provider {}!'.format(provider_name))
    ProviderClass = resolve_provider_class(class_)
    
    # instantiate provider class
    provider = ProviderClass(provider_name, callback, **kwargs)
    
    # return login result
    return provider.login()


def credentials(credentials):
    """
    Deserializes credentials.
    
    :param credentials:
        Credentials serialized with :meth:`.Credentials.serialize` or :class:`.Credentials` instance.
    
    :returns:
        :class:`.Credentials`
    """
    
    return Credentials.deserialize(credentials)


def access(credentials, url, params=None, method='GET', headers={}, max_redirects=5, content_parser=None):
    """
    Accesses **protected resource** on behalf of the **user**.
    
    :param credentials:
        The **user's** :class:`.Credentials` (serialized or normal).
        
    :param str url:
        The **protected resource** URL.
        
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
    
    # Deserialize credentials.
    credentials = Credentials.deserialize(credentials)
    
    # Resolve provider class.
    ProviderClass = credentials.provider_class
    
    # Access resource and return response.
    return ProviderClass.access_with_credentials(credentials=credentials,
                                                 url=url,
                                                 params=params,
                                                 method=method,
                                                 headers=headers,
                                                 max_redirects=max_redirects,
                                                 content_parser=content_parser)


def async_access(*args, **kwargs):
    """
    Same as :func:`.access` but runs asynchronously in a separate thread.
    
    .. warning:: |async|
    
    :returns:
        :class:`.Future` instance representing the separate thread.
    """
    
    return Future(access, *args, **kwargs)






