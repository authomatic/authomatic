# -*- coding: utf-8 -*-
"""
|gae| Extras
------------

Utilities you can use when using this library on |gae|_.
"""

from authomatic import exceptions
from authomatic.extras import interfaces
from google.appengine.ext import ndb
from webapp2_extras import sessions
import os


__all__ = ['ndb_config', 'Webapp2Session']


class GAEError(exceptions.BaseError):
    pass

class Webapp2Session(interfaces.BaseSession):
    def __init__(self, handler, session=None, secret=None, cookie_name='webapp2authomatic',
                 backend='memcache', config=None):
        """
        A simple wrapper for |webapp2|_ sessions. If you provide a session
        it wrapps it and adds the :meth:`.save` method.
        
        If you don't provide a session it creates a new one but you must provide the :data:`.secret`. 
        
        For more about |webapp2| sessions see:
        `http://webapp-improved.appspot.com/api/webapp2_extras/sessions.html`_.
        
        .. warning::
            
            Do not use the ``'securecookie'`` backend with :class:`.providers.OpenID`
            provider. The `python-openid`_ library saves **non json serializable** objects to session
            which the ``'securecookie'`` backend cannot cope with.
            
        :param handler:
            A :class:`webapp2.RequestHandler` instance.
        
        :param session:
            A :class:`webapp2_extras.session.SessionDict` instance.
        
        :param str secret:
            The session secret.
        
        :param str cookie_name:
            The name of the session kookie.
        
        :param backend:
            The session backend. One of ``'memcache'`` or ``'datastore'``.
            
        :param config:
            The session config.
        """
        
        self.handler = handler
        
        if session is None:
            if not secret:
                raise GAEError('Either session or secret must be specified!')
            else:
                # Create new session.
                cfg = config or dict(secret_key=secret, cookie_name=cookie_name)
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
    """
        
    provider_name = ndb.StringProperty( )
    class_ = ndb.StringProperty()
    
    # AuthorizationProvider
    short_name = ndb.IntegerProperty()
    consumer_key = ndb.StringProperty()
    consumer_secret = ndb.StringProperty()
    
    # OAuth2
    scope = ndb.StringProperty()
    
    # AuthenticationProvider
    identifier_param = ndb.StringProperty()
    
    # OpenID
    use_realm = ndb.BooleanProperty(default=True)
    realm_body = ndb.StringProperty()
    realm_param = ndb.StringProperty()
    xrds_param = ndb.StringProperty()
    sreg = ndb.StringProperty()
    sreg_required = ndb.StringProperty()
    ax = ndb.StringProperty()
    ax_required = ndb.StringProperty()
    pape = ndb.StringProperty()
    
    @classmethod
    def get(cls, key, default=None):
        """
        Resembles the dict.get(key[, default=None]) method
        
        Returns a provider config dictionary
        """
        
        result = cls.query(cls.provider_name == key).get()
        
        if result:
            result_dict = result.to_dict()
            
            for i in ('scope', 'sreg', 'sreg_required', 'ax', 'ax_required', 'pape', ):
                prop = result_dict.get(i)
                if prop:
                    result_dict[i] = [s.strip() for s in prop.split(',')]
                else:
                    result_dict[i] = None

            return result_dict
        else:
            return default
    
    
    @classmethod
    def values(cls):
        # get all items
        results = cls.query().fetch()
        # return list of dictionaries
        return [result.to_dict() for result in results]
    
    
    @classmethod
    def initialize(cls):
        """
        Creates an Example entity if the model is empty
        """
        
        if not len(cls.query().fetch()):
            
            example = cls.get_or_insert('Example')
            
            example.class_ = 'Provider class e.g. "authomatic.providers.oauth2.Facebook".'
            example.provider_name = 'Your custom provider name e.g. "fb".'
            
            # TODO: Implement all new arguments including openid store.
            
            # AuthorizationProvider
            example.consumer_key = 'Consumer key.'
            example.consumer_secret = 'Consumer secret'
            example.short_name = 1
            
            # OAuth2
            example.scope = 'coma, separated, list, of, scopes'
            
            # AuthenticationProvider
            example.identifier_param = 'User identifier to authenticate e.g. "me.yahoo.com".'
            
            # OpenID
            example.use_realm = True
            example.realm_body = 'Contents of the HTML body tag of the realm.'
            example.realm_param = 'Name of the query parameter to be used to serve the realm (leave empty for default).'
            example.xrds_param = ' The name of the query parameter to be used to serve the XRDS document (leave empty for default).'
            example.sreg = 'list, of, strings, of, optional, SREG, fields, (leave empty for defaults)'
            example.sreg_required = 'list, of, strings, of, required, SREG, fields, (leave empty for defaults)'
            example.ax = 'list, of, strings, of, optional, AX, schemas, (leave empty for defaults)'
            example.ax_required = 'list, of, strings, of, required, AX, schemas, (leave empty for defaults)'
            example.pape = 'list, of, strings, of, optional, PAPE, policies, (leave empty for defaults)'
            
            example.put()
            
            url = '{}://{}/_ah/admin/datastore?kind={}'.format(os.environ.get('wsgi.url_scheme'),
                                                               os.environ.get('HTTP_HOST'),
                                                               cls.__name__)
            
            raise GAEError('A NDBConfig data model was created! ' + \
                           'Go to {} and populate it with data!'.format(url))


def ndb_config():
    """
    Allows you to have a **datastore** :doc:`config` instead of a hardcoded one.
    
    This function creates an **"Example"** entity of kind **"NDBConfig"** in the datastore
    if the model is empty and raises and error to inform you that you should populate the model with data.
        
    .. note::
    
        The *Datastore Viewer* in the ``_ah/admin/`` won't let you add properties to a model
        if there is not an entity with that property allready.
        Therefore it is a good idea to keep the **"Example"** entity (which has all
        possible properties set) in the datastore.
    
    :raises:
        :exc:`.GAEError`
    
    :returns:
        :class:`.NDBConfig`
    """
    
    NDBConfig.initialize()
    return NDBConfig



