# -*- coding: utf-8 -*-

from xml.etree import ElementTree
import collections
import copy
import datetime
import exceptions
import hashlib
import hmac
import logging
import json
import pickle
import threading
import time
import urllib
import urlparse
import sys

from authomatic.exceptions import SessionError, CredentialsError, RequestElementsError


#===============================================================================
# Global variables !!!
#===============================================================================

_logger = logging.getLogger(__name__)
_logger.addHandler(logging.StreamHandler(sys.stdout))

_counter = None


def normalize_dict(dict_):
    """
    Replaces all values that are single-item iterables with the value of its index 0.

    :param dict dict_:
        Dictionary to normalize.

    :returns:
        Normalized dictionary.
    """

    return dict([(k, v[0] if not type(v) is str and len(v) == 1 else v)
                 for k, v in dict_.items()])


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
        return json.loads(body)
    except:
        pass

    try:
        # Then XML.
        return ElementTree.fromstring(body)
    except:
        pass

    # Finally query string.
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
    except (ImportError, AttributeError) as e:
        if not silent:
            raise exceptions.ImportStringError('Import from string failed for path {0}'.format(import_name),
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
        raise Exception('No provider with id={0} found in the config!'.format(short_name))


class ReprMixin(object):
    """
    Provides __repr__() method with output *ClassName(arg1=value, arg2=value)*.

    Ignored are attributes

    * which values are considered false.
    * with leading underscore.
    * listed in _repr_ignore.

    Values of attributes listed in _repr_sensitive will be replaced by *###*.
    Values which repr() string is longer than _repr_length_limit will be represented as *ClassName(...)*
    """

    #: Iterable of attributes to be ignored.
    _repr_ignore = []
    #: Iterable of attributes which value should not be visible.
    _repr_sensitive = []
    #: `int` Values longer than this will be truncated to *ClassName(...)*.
    _repr_length_limit = 20


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
                if len(repr(v)) > self._repr_length_limit:
                    # Truncate to ClassName(...)
                    v = '{0}(...)'.format(v.__class__.__name__)
                else:
                    v = repr(v)

                args.append('{0}={1}'.format(k, v))

        args = ', '.join(args)

        return '{0}({1})'.format(name, args)


class Future(threading.Thread):
    """
    Represents an activity run in a separate thread.
    Subclasses the standard library :class:`threading.Thread` and adds :attr:`.get_result` method.

    .. warning::

        |async|

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
    """A dictionary-like secure cookie session implementation."""
    def __init__(self, adapter, secret, name='authomatic', max_age=600,
                 secure=False):
        """
        :param str secret:
            Session secret used to sign the session cookie.
        :param str name:
            Session cookie name.
        :param int max_age:
            Maximum allowed age of session cookie nonce in seconds.
        :param bool secure:
            If ``True`` the session cookie will be saved with ``Secure``
            attribute.
        """

        self.adapter = adapter
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
        value = 'deleted' if delete else self._serialize(self.data)
        split_url = urlparse.urlsplit(self.adapter.url)
        domain = split_url.netloc.split(':')[0]

        # Work-around for issue #11, failure of WebKit-based browsers to accept
        # cookies set as part of a redirect response in some circumstances.
        if '.' not in domain:
            template = '{name}={value}; Path={path}; HttpOnly{secure}{expires}'
        else:
            template = ('{name}={value}; Domain={domain}; Path={path}; '
                        'HttpOnly{secure}{expires}')

        return template.format(
            name=self.name,
            value=value,
            domain=domain,
            path=split_url.path,
            secure='; Secure' if self.secure else '',
            expires='; Expires=Thu, 01-Jan-1970 00:00:01 GMT' if delete else ''
        )

    def save(self):
        """Adds the session cookie to headers."""
        if self.data:
            # Set the cookie header.
            self.adapter.set_header('Set-Cookie', self.create_cookie())

            # Reset data
            self._data = {}

    def delete(self):
        self.adapter.set_header('Set-Cookie', self.create_cookie(delete=True))

    def _get_data(self):
        """Extracts the session data from cookie."""
        cookie = self.adapter.cookies.get(self.name)
        return self._deserialize(cookie) if cookie else {}

    @property
    def data(self):
        """Gets session data lazily."""
        if not self._data:
            self._data = self._get_data()
        # Always return a dict, even if deserialization returned nothing
        if self._data is None:
            self._data = {}
        return self._data

    def _signature(self, *parts):
        """Creates signature for the session."""
        signature = hmac.new(self.secret, digestmod=hashlib.sha1)
        signature.update('|'.join(parts))
        return signature.hexdigest()

    def _serialize(self, value):
        """
        Converts the value to a signed string with timestamp.

        :param value:
            Object to be serialized.

        :returns:
            Serialized value.
        """

        data = copy.deepcopy(value)

        # 1. Serialize
        serialized = json.dumps(data)

        # 2. Encode
        # Percent encoding produces smaller result then urlsafe base64.
        encoded = urllib.quote(serialized, '')

        # 3. Concatenate
        timestamp = str(int(time.time()))
        signature = self._signature(self.name, encoded, timestamp)
        return '|'.join([encoded, timestamp, signature])


    def _deserialize(self, value):
        """
        Deserializes and verifies the value created by :meth:`._serialize`.

        :param str value:
            The serialized value.

        :returns:
            Deserialized object.
        """

        # 3. Split
        encoded, timestamp, signature = value.split('|')

        # Verify signature
        if not signature == self._signature(self.name, encoded, timestamp):
            raise SessionError('Invalid signature "{0}"!'.format(signature))

        # Verify timestamp
        if int(timestamp) < int(time.time()) - self.max_age:
            return None

        # 2. Decode
        decoded = urllib.unquote(encoded)

        # 1. Deserialize
        deserialized = json.loads(decoded)

        return deserialized

    def __setitem__(self, key, value):
        self._data[key] = value

    def __getitem__(self, key):
        return self.data.__getitem__(key)

    def __delitem__(self, key):
        return self._data.__delitem__(key)

    def get(self, key, default=None):
        return self.data.get(key, default)


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

        .. warning::

            |async|

        :returns:
            :class:`.Future` instance representing the separate thread.
        """

        return Future(self.update)

    def to_dict(self):
        """
        Converts the :class:`.User` instance to a :class:`dict`.

        :returns:
            :class:`dict`
        """

        # copy the dictionary
        d = copy.copy(self.__dict__)

        # Keep only the provider name to avoid circular reference
        d['provider'] = self.provider.name
        d['credentials'] = self.credentials.serialize() if self.credentials else None
        d['birth_date'] = str(d['birth_date'])

        # Remove content
        d.pop('content')

        if isinstance(self.data, ElementTree.Element):
            d['data'] = None

        return d


class SupportedUserAttributes(collections.namedtuple('SupportedUserAttributes',
                                         [
                                             'id',
                                             'username',
                                             'name',
                                             'first_name',
                                             'last_name',
                                             'nickname',
                                             'link',
                                             'gender',
                                             'timezone',
                                             'locale',
                                             'email',
                                             'phone',
                                             'picture',
                                             'birth_date',
                                             'country',
                                             'city',
                                             'postal_code',
                                         ])):
    def __new__(cls, **kwargs):
        defaults = dict((i, False) for i in SupportedUserAttributes._fields)
        defaults.update(**kwargs)
        return super(SupportedUserAttributes, cls).__new__(cls, **defaults)


class Credentials(ReprMixin):
    """Contains all necessary information to fetch **user's protected resources**."""

    _repr_sensitive = ('token', 'refresh_token', 'token_secret', 'consumer_key', 'consumer_secret')

    def __init__(self, config, **kwargs):
        
        #: :class:`dict` :doc:`config`.
        self.config = config

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

            #: :class:`str` Provider type e.g. ``"authomatic.providers.oauth2.OAuth2"``.
            self.provider_type_id = provider.type_id

            #: :class:`str` Provider short name specified in the :doc:`config`.
            self.provider_id = int(provider.id) if provider.id else None

            #: :class:`class` Provider class.
            self.provider_class = provider.__class__

            #: :class:`str` Consumer key specified in the :doc:`config`.
            self.consumer_key = provider.consumer_key

            #: :class:`str` Consumer secret specified in the :doc:`config`.
            self.consumer_secret = provider.consumer_secret

        else:
            self.provider_name = kwargs.get('provider_name', '')
            self.provider_type = kwargs.get('provider_type', '')
            self.provider_type_id = kwargs.get('provider_type_id')
            self.provider_id = kwargs.get('provider_id')
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
            in the **user authorization request**.

        :param bool force:
            If ``True`` the credentials will be refreshed even if they won't expire soon.

        :param int soon:
            Number of seconds specifying what means *soon*.
        """

        if hasattr(self.provider_class, 'refresh_credentials'):
            if force or self.expire_soon(soon):
                logging.info('PROVIDER NAME: {0}'.format(self.provider_name))
                return self.provider_class(self, None, self.provider_name).refresh_credentials(self)


    def async_refresh(self, *args, **kwargs):
        """
        Same as :meth:`.refresh` but runs asynchronously in a separate thread.

        .. warning::

            |async|

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

        if self.provider_id is None:
            raise exceptions.ConfigError('To serialize credentials you need to specify a unique ' + \
                                         'integer under the "id" key in the config for each provider!')

        # Get the provider type specific items.
        rest = self.provider_type_class().to_tuple(self)

        # Provider ID and provider type ID are always the first two items.
        result = (self.provider_id, self.provider_type_id) + rest

        # Make sure that all items are strings.
        stringified = [str(i) for i in result]

        # Concatenate by newline.
        concatenated = '\n'.join(stringified)

        # Percent encode.
        return urllib.quote(concatenated, '')


    @classmethod
    def deserialize(cls, config, credentials):
        """
        A *class method* which reconstructs credentials created by :meth:`serialize`.
        You can also pass it a :class:`.Credentials` instance.

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

        # We need the provider ID to move forward.
        if split[0] is None:
            raise CredentialsError('To deserialize credentials you need to specify a unique ' + \
                                   'integer under the "id" key in the config for each provider!')

        provider_id = int(split[0])

        # Get provider config by short name.
        provider_name = id_to_name(config, provider_id)
        cfg = config.get(provider_name)

        # Get the provider class.
        ProviderClass = resolve_provider_class(cfg.get('class_'))

        deserialized = Credentials(config)

        deserialized.provider_id = provider_id
        deserialized.provider_type = ProviderClass.get_type()
        deserialized.provider_type_id = split[1]
        deserialized.provider_class = ProviderClass
        deserialized.provider_name = provider_name
        deserialized.provider_class = ProviderClass

        # Add provider type specific properties.
        return ProviderClass.reconstruct(split[2:], deserialized, cfg)


class LoginResult(ReprMixin):
    """
    Result of the :func:`authomatic.login` function.
    """

    def __init__(self, provider):
        #: A :doc:`provider <providers>` instance.
        self.provider = provider

        #: An instance of the :exc:`authomatic.exceptions.BaseError` subclass.
        self.error = None


    def popup_js(self, callback_name=None, indent=None, custom=None, stay_open=False):
        """
        Returns JavaScript that:

        #.  Triggers the ``options.onLoginComplete(result, closer)`` handler set with the
            :ref:`authomatic.setup() <js_setup>` function of :ref:`javascript.js <js>`.
        #.  Calls the JavasScript callback specified by :data:`callback_name`
            on the opener of the *login handler popup* and passes it the
            *login result* JSON object as first argument and the `closer` function which
            you should call in your callback to close the popup.

        :param str callback_name:
            The name of the javascript callback e.g ``foo.bar.loginCallback``
            will result in ``window.opener.foo.bar.loginCallback(result);`` in the HTML.

        :param int indent:
            The number of spaces to indent the JSON result object.
            If ``0`` or negative, only newlines are added.
            If ``None``, no newlines are added.

        :param custom:
            Any JSON serializable object that will be passed to the ``result.custom`` attribute.

        :param str stay_open:
            If ``True``, the popup will stay open.

        :returns:
            :class:`str` with JavaScript.
        """

        custom_callback = """
        try {{ window.opener.{cb}(result, closer); }} catch(e) {{}}
        """.format(cb=callback_name) if callback_name else ''

        # TODO: Move the window.close() to the opener
        return """
        (function(){{

            closer = function(){{
                window.close();
            }};

            var result = {result};
            result.custom = {custom};

            {custom_callback}

            try {{ window.opener.authomatic.loginComplete(result, closer); }} catch(e) {{}}

        }})();

        """.format(result=self.to_json(indent),
                   custom=json.dumps(custom),
                   custom_callback=custom_callback,
                   stay_open='// ' if stay_open else '')


    def popup_html(self, callback_name=None, indent=None, title='Login | {0}', custom=None, stay_open=False):
        """
        Returns a HTML with JavaScript that:

        #.  Triggers the ``options.onLoginComplete(result, closer)`` handler set with the
            :ref:`authomatic.setup() <js_setup>` function of :ref:`javascript.js <js>`.
        #.  Calls the JavasScript callback specified by :data:`callback_name`
            on the opener of the *login handler popup* and passes it the
            *login result* JSON object as first argument and the `closer` function which
            you should call in your callback to close the popup.

        :param str callback_name:
            The name of the javascript callback e.g ``foo.bar.loginCallback``
            will result in ``window.opener.foo.bar.loginCallback(result);`` in the HTML.

        :param int indent:
            The number of spaces to indent the JSON result object.
            If ``0`` or negative, only newlines are added.
            If ``None``, no newlines are added.

        :param str title:
            The text of the HTML title. You can use ``{0}`` tag inside,
            which will be replaced by the provider name.

        :param custom:
            Any JSON serializable object that will be passed to the ``result.custom`` attribute.

        :param str stay_open:
            If ``True``, the popup will stay open.

        :returns:
            :class:`str` with HTML.
        """

        return """
        <!DOCTYPE html>
        <html>
            <head><title>{title}</title></head>
            <body>
            <script type="text/javascript">
                {js}
            </script>
            </body>
        </html>
        """.format(title=title.format(self.provider.name if self.provider else ''),
                   js=self.popup_js(callback_name, indent, custom, stay_open))

    @property
    def user(self):
        """
        A :class:`.User` instance.
        """

        return self.provider.user if self.provider else None


    def to_dict(self):
        return dict(provider=self.provider, user=self.user, error=self.error)


    def to_json(self, indent=4):
        return json.dumps(self, default=lambda obj: obj.to_dict() if hasattr(obj, 'to_dict') else '', indent=indent)


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
    Inherits from :class:`.Response`, adds  :attr:`~UserInfoResponse.user` attribute.
    """

    def __init__(self, user, *args, **kwargs):
        super(UserInfoResponse, self).__init__(*args, **kwargs)

        #: :class:`.User` instance.
        self.user = user


class RequestElements(tuple):
    """
    A tuple of ``(url, method, params, headers, body)`` request elements.
    With some additional properties.
    """

    def __new__(cls, url, method, params, headers, body):
        return tuple.__new__(cls, (url, method, params, headers, body))

    @property
    def url(self):
        """
        Request URL.
        """

        return self[0]

    @property
    def method(self):
        """
        HTTP method of the request.
        """

        return self[1]

    @property
    def params(self):
        """
        Dictionary of request parameters.
        """

        return self[2]

    @property
    def headers(self):
        """
        Dictionary of request headers.
        """

        return self[3]

    @property
    def body(self):
        """
        :class:`str` Body of ``POST``, ``PUT`` and ``PATCH`` requests.
        """

        return self[4]

    @property
    def query_string(self):
        """
        Query string of the request.
        """

        return urllib.urlencode(self.params)

    @property
    def full_url(self):
        """
        URL with query string.
        """

        return self.url + '?' + self.query_string

    def to_json(self):
        return json.dumps(dict(url=self.url,
                          method=self.method,
                          params=self.params,
                          headers=self.headers,
                          body=self.body))


class Authomatic(object):
    def __init__(self, config, secret, session_max_age=600, secure_cookie=False,
                 session=None, session_save_method=None, report_errors=True,
                 debug=False, logging_level=logging.INFO, prefix='authomatic',
                 logger=None):
        """
        Encapsulates all the functionality of this package.
        
        :param dict config:
            :doc:`config`

        :param str secret:
            A secret string that will be used as the key for signing :class:`.Session` cookie and
            as a salt by *CSRF* token generation.
    
        :param session_max_age:
            Maximum allowed age of :class:`.Session` cookie nonce in seconds.
    
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
            The logging level threshold for the default logger as specified in
            the standard Python
            `logging library <http://docs.python.org/2/library/logging.html>`_.
            This setting is ignored when :data:`logger` is set.
            Default is ``logging.INFO``.
    
        :param str prefix:
            Prefix used as the :class:`.Session` cookie name.

        :param logger:
            A :class:`logging.logger` instance.
        """
        
        self.config = config
        self.secret = secret
        self.session_max_age = session_max_age
        self.secure_cookie = secure_cookie
        self.session = session
        self.session_save_method = session_save_method
        self.report_errors = report_errors
        self.debug = debug
        self.logging_level = logging_level
        self.prefix = prefix
        self._logger = logger or logging.getLogger(str(id(self)))
        
        # Set logging level.
        if logger is None:
            self._logger.setLevel(logging_level)
    
    
    def login(self, adapter, provider_name, callback=None, session=None, session_saver=None, **kwargs):
        """
        If :data:`provider_name` specified, launches the login procedure
        for corresponding :doc:`provider </reference/providers>` and
        returns :class:`.LoginResult`.
    
        If :data:`provider_name` is empty, acts like :meth:`.Authomatic.backend`.
    
        .. warning::

            The method redirects the **user** to the **provider** which in turn redirects
            **him/her** back to the *request handler* where it has been called.
    
        :param str provider_name:
            Name of the provider as specified in the keys of the :doc:`config`.
    
        :param callable callback:
            If specified the method will call the callback with :class:`.LoginResult`
            passed as argument and will return nothing.
    
        :param bool report_errors:
    
        .. note::
    
            Accepts additional keyword arguments that will be passed to :doc:`provider <providers>` constructor.
    
        :returns:
            :class:`.LoginResult`
        """
        
        if provider_name:
            # retrieve required settings for current provider and raise exceptions if missing
            provider_settings = self.config.get(provider_name)
            if not provider_settings:
                raise exceptions.ConfigError('Provider name "{0}" not specified!'.format(provider_name))
    
            if not (session is None or session_saver is None):
                session = session
                session_saver = session_saver
            else:
                session = Session(adapter=adapter,
                                   secret=self.secret,
                                   max_age=self.session_max_age,
                                   name=self.prefix,
                                   secure=self.secure_cookie)
    
                session_saver = session.save
    
            # Resolve provider class.
            class_ = provider_settings.get('class_')
            if not class_:
                raise exceptions.ConfigError('The "class_" key not specified in the config for provider {0}!'.format(provider_name))
            ProviderClass = resolve_provider_class(class_)

            # FIXME: Find a nicer solution
            ProviderClass._logger = self._logger
    
            # instantiate provider class
            provider = ProviderClass(self,
                                     adapter=adapter,
                                     provider_name=provider_name,
                                     callback=callback,
                                     session=session,
                                     session_saver=session_saver,
                                     **kwargs)
    
            # return login result
            return provider.login()
    
        else:
            # Act like backend.
            self.backend(adapter)

 
    def credentials(self, credentials):
        """
        Deserializes credentials.
    
        :param credentials:
            Credentials serialized with :meth:`.Credentials.serialize` or :class:`.Credentials` instance.
    
        :returns:
            :class:`.Credentials`
        """
    
        return Credentials.deserialize(self.config, credentials)
    
    
    def access(self, credentials, url, params=None, method='GET', headers=None, body='', max_redirects=5, content_parser=None):
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
    
        :param str body:
            Body of ``POST``, ``PUT`` and ``PATCH`` requests.
    
        :param int max_redirects:
            Maximum number of HTTP redirects to follow.
    
        :param function content_parser:
            A function to be used to parse the :attr:`.Response.data` from :attr:`.Response.content`.
    
        :returns:
            :class:`.Response`
        """
    
        # Deserialize credentials.
        credentials = Credentials.deserialize(self.config, credentials)
    
        # Resolve provider class.
        ProviderClass = credentials.provider_class
        logging.info('ACCESS HEADERS: {0}'.format(headers))
        # Access resource and return response.
        
        provider = ProviderClass(self, adapter=None, provider_name=credentials.provider_name)
        provider.credentials = credentials
        
        return provider.access(url=url,
                               params=params,
                               method=method,
                               headers=headers,
                               body=body,
                               max_redirects=max_redirects,
                               content_parser=content_parser)
    
    
    def async_access(self, *args, **kwargs):
        """
        Same as :meth:`.Authomatic.access` but runs asynchronously in a separate thread.
    
        .. warning::

            |async|
    
        :returns:
            :class:`.Future` instance representing the separate thread.
        """
    
        return Future(self.access, *args, **kwargs)
    
    
    def request_elements(self, credentials=None, url=None, method='GET', params=None,
                         headers=None, body='', json_input=None, return_json=False):
        """
        Creates request elements for accessing **protected resource of a user**.
        Required arguments are :data:`credentials` and :data:`url`.
        You can pass :data:`credentials`, :data:`url`, :data:`method`, and :data:`params`
        as a JSON object.
    
        :param credentials:
            The **user's** credentials (can be serialized).
    
        :param str url:
            The url of the protected resource.
    
        :param str method:
            The HTTP method of the request.
    
        :param dict params:
            Dictionary of request parameters.
    
        :param dict headers:
            Dictionary of request headers.
    
        :param str body:
            Body of ``POST``, ``PUT`` and ``PATCH`` requests.
    
        :param str json_input:
            you can pass :data:`credentials`, :data:`url`, :data:`method`, :data:`params` and :data:`headers`
            in a JSON object. Values from arguments will be used for missing properties.
    
            ::
    
                {
                    "credentials": "###",
                    "url": "https://example.com/api",
                    "method": "POST",
                    "params": {
                        "foo": "bar"
                    },
                    "headers": {
                        "baz": "bing",
                        "Authorization": "Bearer ###"
                    },
                    "body": "Foo bar baz bing."
                }
    
        :param bool return_json:
            if ``True`` the function returns a json object.
    
            ::
    
                {
                    "url": "https://example.com/api",
                    "method": "POST",
                    "params": {
                        "access_token": "###",
                        "foo": "bar"
                    },
                    "headers": {
                        "baz": "bing",
                        "Authorization": "Bearer ###"
                    },
                    "body": "Foo bar baz bing."
                }
    
        :returns:
            :class:`.RequestElements` or JSON string.
        """
    
        # Parse values from JSON
        if json_input:
            parsed_input = json.loads(json_input)
    
            credentials = parsed_input.get('credentials', credentials)
            url = parsed_input.get('url', url)
            method = parsed_input.get('method', method)
            params = parsed_input.get('params', params)
            headers = parsed_input.get('headers', headers)
            body = parsed_input.get('body', body)
    
        if not credentials and url:
            raise RequestElementsError('To create request elements, you must provide credentials ' +\
                                        'and URL either as keyword arguments or in the JSON object!')
    
        # Get the provider class
        credentials = Credentials.deserialize(self.config, credentials)
        ProviderClass = credentials.provider_class
    
        # Create request elements
        request_elements = ProviderClass.create_request_elements(ProviderClass.PROTECTED_RESOURCE_REQUEST_TYPE,
                                                                 credentials=credentials,
                                                                 url=url,
                                                                 method=method,
                                                                 params=params,
                                                                 headers=headers,
                                                                 body=body)
    
        if return_json:
            return request_elements.to_json()
    
        else:
            return request_elements
    
    
    def backend(self, adapter):
        """
        Converts a *request handler* to a JSON backend which you can use with :ref:`authomatic.js <js>`.
    
        Just call it inside a *request handler* like this:
    
        ::
    
            class JSONHandler(webapp2.RequestHandler):
                def get(self):
                    authomatic.backend(Webapp2Adapter(self))
    
        :param adapter:
            The only argument is an :doc:`adapter <adapters>`.
    
        The *request handler* will now accept these request parameters:
    
        :param str type:
            Type of the request. Either ``auto``, ``fetch`` or ``elements``. Default is ``auto``.
    
        :param str credentials:
            Serialized :class:`.Credentials`.
    
        :param str url:
            URL of the **protected resource** request.
    
        :param str method:
            HTTP method of the **protected resource** request.
    
        :param str body:
            HTTP body of the **protected resource** request.
    
        :param JSON params:
            HTTP params of the **protected resource** request as a JSON object.
    
        :param JSON headers:
            HTTP headers of the **protected resource** request as a JSON object.
    
        :param JSON json:
            You can pass all of the aforementioned params except ``type`` in a JSON object.
    
            .. code-block:: javascript
    
                {
                    "credentials": "######",
                    "url": "https://example.com",
                    "method": "POST",
                    "params": {"foo": "bar"},
                    "headers": {"baz": "bing"},
                    "body": "the body of the request"
                }
    
        Depending on the ``type`` param, the handler will either write
        a JSON object with *request elements* to the response,
        and add an ``Authomatic-Response-To: elements`` response header, ...
    
        .. code-block:: javascript
    
            {
                "url": "https://example.com/api",
                "method": "POST",
                "params": {
                    "access_token": "###",
                    "foo": "bar"
                },
                "headers": {
                    "baz": "bing",
                    "Authorization": "Bearer ###"
                }
            }
    
        ... or make a fetch to the **protected resource** and forward it's response
        content, status and headers with an additional ``Authomatic-Response-To: fetch`` header
        to the response.
    
        .. warning::

            The backend will not work if you write anything to the response in the handler!

        """
    
        AUTHOMATIC_HEADER = 'Authomatic-Response-To'
    
        # Collect request params
        request_type = adapter.params.get('type', 'auto')
        json_input = adapter.params.get('json')
        credentials = adapter.params.get('credentials')
        url = adapter.params.get('url')
        method = adapter.params.get('method', 'GET')
        body = adapter.params.get('body', '')
    
    
        params = adapter.params.get('params')
        params = json.loads(params) if params else {}
    
        headers = adapter.params.get('headers')
        headers = json.loads(headers) if headers else {}
    
        ProviderClass = Credentials.deserialize(self.config, credentials).provider_class
    
        if request_type == 'auto':
            # If there is a "callback" param, it's a JSONP request.
            jsonp = params.get('callback')
    
            # JSONP is possible only with GET method.
            if ProviderClass.supports_jsonp and method is 'GET':
                request_type = 'elements'
            else:
                # Remove the JSONP callback
                if params.get('callback'):
                    params.pop('callback')
                request_type = 'fetch'
    
        if request_type == 'fetch':
            # Access protected resource
            response = self.access(credentials, url, params, method, headers, body)
            result = response.content
    
            # Forward status
            adapter.status = str(response.status) + ' ' + str(response.reason)
    
            # Forward headers
            for k, v in response.getheaders():
                logging.info('    {0}: {1}'.format(k, v))
                adapter.set_header(k, v)
    
        elif request_type == 'elements':
            # Create request elements
            if json_input:
                result = self.request_elements(json_input=json_input, return_json=True)
            else:
                result = self.request_elements(credentials=credentials,
                                          url=url,
                                          method=method,
                                          params=params,
                                          headers=headers,
                                          body=body,
                                          return_json=True)
    
            adapter.set_header('Content-Type', 'application/json')
        else:
            result = '{"error": "Bad Request!"}'
    
    
        # Add the authomatic header
        adapter.set_header(AUTHOMATIC_HEADER, request_type)
    
        # Write result to response
        adapter.write(result)
    

#===============================================================================
# Deprecated
#===============================================================================

def setup(*args, **kwargs):
    """
     
    .. warning::

        This function is **deprecated** and will be removed in version 0.1.0!
        Use instance of :class:`.Authomatic` class instead.

    """
     
    logging.warn('The authomatic.setup function is deprecated and will be removed in version 0.1.0! ' + \
                 'Use an instance of the Authomatic class instead.')
     
    global global_authomatic_instance
    global_authomatic_instance = Authomatic(*args, **kwargs)
 
 
def login(*args, **kwargs):
    """
     
    .. warning::

        This function is **deprecated** and will be removed in version 0.1.0!
        Use the :meth:`.Authomatic.login` method instead.

    """
     
    logging.warn('The authomatic.login function is deprecated and will be removed in version 0.1.0! ' + \
                 'Use the "login" method of the "Authomatic" class instead.')
     
    return global_authomatic_instance.login(*args, **kwargs)
 
 
def credentials(*args, **kwargs):
    """
     
    .. warning::

        This function is **deprecated** and will be removed in version 0.1.0!
        Use the :meth:`.Authomatic.credentials` method instead.

    """
     
    logging.warn('The authomatic.credentials function is deprecated and will be removed in version 0.1.0! ' + \
                 'Use the "credentials" method of the "Authomatic" class instead.')
     
    return global_authomatic_instance.credentials(*args, **kwargs)
 
 
def access(*args, **kwargs):
    """
     
    .. warning::

        This function is **deprecated** and will be removed in version 0.1.0!
        Use the :meth:`.Authomatic.access` method instead.

    """
     
    logging.warn('The authomatic.access function is deprecated and will be removed in version 0.1.0! ' + \
                 'Use the "access" method of the "Authomatic" class instead.')
     
    return global_authomatic_instance.access(*args, **kwargs)
 
 
def async_access(*args, **kwargs):
    """
     
    .. warning::

        This function is **deprecated** and will be removed in version 0.1.0!
        Use the :meth:`.Authomatic.async_access` method instead.

    """
     
    logging.warn('The authomatic.async_access function is deprecated and will be removed in version 0.1.0! ' + \
                 'Use the "async_access" method of the "Authomatic" class instead.')
     
    return global_authomatic_instance.async_access(*args, **kwargs)
 
 
def request_elements(*args, **kwargs):
    """
     
    .. warning::

        This function is **deprecated** and will be removed in version 0.1.0!
        Use the :meth:`.Authomatic.request_elements` method instead.

    """
     
    logging.warn('The authomatic.request_elements function is deprecated and will be removed in version 0.1.0! ' + \
                 'Use the "request_elements" method of the "Authomatic" class instead.')
     
    return global_authomatic_instance.request_elements(*args, **kwargs)
 
 
def backend(*args, **kwargs):
    """
     
    .. warning::

        This function is **deprecated** and will be removed in version 0.1.0!
        Use the :meth:`.Authomatic.backend` method instead.

    """
     
    logging.warn('The authomatic.backend function is deprecated and will be removed in version 0.1.0! ' + \
                 'Use the "backend" method of the "Authomatic" class instead.')
     
    return global_authomatic_instance.backend(*args, **kwargs)





