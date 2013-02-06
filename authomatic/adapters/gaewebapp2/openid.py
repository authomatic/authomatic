# We need absolute iport to import from openid library which has the same name as this module
from __future__ import absolute_import

from google.appengine.ext import ndb
import datetime
import openid.store.interface


class NDBOpenIDStore(ndb.Expando, openid.store.interface.OpenIDStore):
    serialized = ndb.StringProperty()
    expiration_date = ndb.DateTimeProperty()
    # we need issued to sort by most recently issued
    issued = ndb.IntegerProperty()
    
    
    @classmethod
    def storeAssociation(cls, server_url, association):
        # store an entity with key = server_url
                
        issued = datetime.datetime.fromtimestamp(association.issued)
        lifetime = datetime.timedelta(0, association.lifetime)
        
        expiration_date = issued + lifetime
        
        entity = cls.get_or_insert(association.handle, parent=ndb.Key('ServerUrl', server_url))
        
        entity.serialized = association.serialize()
        entity.expiration_date = expiration_date
        entity.issued = association.issued
        entity.put()
    
    
    @classmethod
    def cleanupAssociations(cls):
        
        # query for all expired
        query = cls.query(cls.expiration_date <= datetime.datetime.now())
        
        # fetch keys only
        expired = query.fetch(keys_only=True)
        
        # delete all expired
        ndb.delete_multi(expired)
        
        return len(expired)
    
    
    @classmethod
    def getAssociation(cls, server_url, handle=None):
        
        cls.cleanupAssociations()
        
        if handle:
            key = ndb.Key('ServerUrl', server_url, cls, handle)
            entity = key.get()
        else:
            # return most recently issued association
            entity = cls.query(ancestor=ndb.Key('ServerUrl', server_url)).order(-cls.issued).get()
        
        if entity and entity.serialized:
            return openid.association.Association.deserialize(entity.serialized)
    
    
    @classmethod
    def removeAssociation(cls, server_url, handle):
        key = ndb.Key('ServerUrl', server_url, cls, handle)
        if key.get():
            key.delete()
            return True
    
    @classmethod
    def useNonce(cls, server_url, timestamp, salt):
        
        # check whether there is already an entity with the same ancestor path in the datastore
        key = ndb.Key('ServerUrl', str(server_url) or 'x', 'TimeStamp', str(timestamp), cls, str(salt))
        
        result = key.get()
        
        if result:
            # if so, the nonce is not valid so return False
            return False
        else:
            # if not, store the key to datastore and return True
            nonce = cls(key=key)
            nonce.expiration_date = datetime.datetime.fromtimestamp(timestamp) + datetime.timedelta(0, openid.store.nonce.SKEW)
            nonce.put()
            return True
    
    
    @classmethod
    def cleanupNonces(cls):
        # get all expired nonces
        expired = cls.query().filter(cls.expiration_date <= datetime.datetime.now()).fetch(keys_only=True)
        
        # delete all expired
        ndb.delete_multi(expired)
        
        return len(expired)
