# -*- coding: utf-8 -*-
"""
|gae| Extras
------------

Utilities you can use when using this library on |gae|_.
"""


from authomatic import exceptions
from authomatic.extras import interfaces
from authomatic.extras.gae.openid import NDBOpenIDStore
import logging

logger = logging.getLogger(__name__)

try:
    from google.appengine.ext import ndb
    from webapp2_extras import sessions
except ImportError:
    logger.exception("FATAL: google.appengine 1st Gen. not installed!")
    raise

__all__ = ['ndb_config', 'Webapp2Session']


class GAEError(exceptions.BaseError):
    pass


class Webapp2Session(interfaces.BaseSession):
    """
    A simple wrapper for |webapp2|_ sessions. If you provide a session it wraps
    it and adds the :meth:`.save` method.

    If you don't provide a session it creates a new one but you must provide
    the :data:`.secret`.

    For more about |webapp2| sessions see:
    http://webapp-improved.appspot.com/api/webapp2_extras/sessions.html.

    """

    def __init__(self, handler, session=None, secret=None,
                 cookie_name='webapp2authomatic', backend='memcache',
                 config=None):
        """
        .. warning::

            Do not use the ``'securecookie'`` backend with
            :class:`.providers.OpenID` provider. The
            `python-openid`_ library saves **non json serializable** objects
            to session which the ``'securecookie'`` backend cannot cope with.

        :param handler:
            A :class:`webapp2.RequestHandler` instance.

        :param session:
            A :class:`webapp2_extras.session.SessionDict` instance.

        :param str secret:
            The session secret.

        :param str cookie_name:
            The name of the session cookie.

        :param backend:
            The session backend. One of ``'memcache'`` or ``'datastore'``.

        :param config:
            The session config.

        """

        self.handler = handler

        if session is None:
            if not secret:
                raise GAEError('Either session or secret must be specified!')
            # Create new session.
            cfg = config or {'secret_key': secret, 'cookie_name': cookie_name}
            session_store = sessions.SessionStore(handler.request, cfg)
            self.session_dict = session_store.get_session(backend=backend)
        else:
            # Use supplied session.
            self.session_dict = session

    def save(self):
        return self.session_dict.container.save_session(self.handler.response)

    def __setitem__(self, key, value):
        return self.session_dict.__setitem__(key, value)

    def __getitem__(self, key):
        return self.session_dict.__getitem__(key)

    def __delitem__(self, key):
        return self.session_dict.__delitem__(key)

    def get(self, key):
        return self.session_dict.get(key)


class NDBConfig(ndb.Model):
    """
    |gae| `NDB <https://developers.google.com/appengine/docs/python/ndb/>`_
    based :doc:`config`.

    .. note::

        By :class:`.OpenID` provider uses :class:`.NDBOpenIDStore`
        as default :attr:`.OpenID.store`.

    """

    # General properties
    provider_name = ndb.StringProperty()
    class_ = ndb.StringProperty()

    # AuthorizationProvider properties
    provider_id = ndb.IntegerProperty()
    consumer_key = ndb.StringProperty()
    consumer_secret = ndb.StringProperty()

    # OAuth2 properties
    scope = ndb.StringProperty()
    offline = ndb.BooleanProperty()

    # AuthenticationProvider properties
    identifier_param = ndb.StringProperty()

    @classmethod
    def get(cls, key, default=None):
        """
        Resembles the :meth:`dict.get` method.

        :returns:
            A configuration dictionary for specified provider.

        """

        # Query datastore.
        result = cls.query(cls.provider_name == key).get()

        if result:
            result_dict = result.to_dict()

            # Use NDBOpenIDStore by default
            result_dict['store'] = NDBOpenIDStore

            # Convert coma-separated values to list. Currently only scope is
            # csv.
            for i in ('scope', ):
                prop = result_dict.get(i)
                if prop:
                    result_dict[i] = [s.strip() for s in prop.split(',')]
                else:
                    result_dict[i] = None

            return result_dict
        return default

    @classmethod
    def values(cls):
        """
        Resembles the :meth:`dict.values` method.
        """

        # get all items
        results = cls.query().fetch()
        # return list of dictionaries
        return [result.to_dict() for result in results]

    @classmethod
    def initialize(cls):
        """
        Creates an **"Example"** entity of kind **"NDBConfig"** in the
        datastore if the model is empty and raises and error to inform you that
        you should populate the model with data.

        .. note::

            The *Datastore Viewer* in the ``_ah/admin/`` won't let you add
            properties to a model if there is not an entity with that
            property already. Therefore it is a good idea to keep the
            **"Example"** entity (which has all possible properties set) in
            the datastore.

        """

        if not len(cls.query().fetch()):

            example = cls.get_or_insert('Example')

            example.class_ = 'Provider class e.g. ' + \
                             '"authomatic.providers.oauth2.Facebook".'
            example.provider_name = 'Your custom provider name e.g. "fb".'

            # AuthorizationProvider
            example.consumer_key = 'Consumer key.'
            example.consumer_secret = 'Consumer secret'
            example.provider_id = 1

            # OAuth2
            example.scope = 'coma, separated, list, of, scopes'

            # AuthenticationProvider
            example.identifier_param = 'Querystring parameter for claimed ' + \
                                       'id. default is "id"'

            # Save the example
            example.put()

            # Raise an information error.
            raise GAEError(
                'A NDBConfig data model was created! Go to Datastore Viewer '
                'in your dashboard and populate it with data!')


def ndb_config():
    """
    Allows you to have a **datastore** :doc:`config` instead of a hardcoded
    one.

    This function creates an **"Example"** entity of kind **"NDBConfig"** in
    the datastore if the model is empty and raises and error to inform you
    that you should populate the model with data.

    .. note::

        The *Datastore Viewer* of the |gae|_ admin won't let you add
        properties to a model if there is not an entity with that property
        already. Therefore it is a good idea to keep the **"Example"**
        entity (which has all properties set) in the datastore.

    :raises:
        :exc:`.GAEError`

    :returns:
        :class:`.NDBConfig`

    """

    NDBConfig.initialize()
    return NDBConfig
