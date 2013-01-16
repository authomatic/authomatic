
from google.appengine.ext import testbed, ndb
from simpleauth2.adapters.gae_webapp2 import NDBOpenIDStore
import datetime
import pytest
import time


class AssociationMock(object):
    def __init__(self, handle, serialized, issued, lifetime):
        self.handle = handle
        self.serialized = serialized
        self.issued = issued
        self.lifetime = lifetime
    
    def serialize(self):
        return self.serialized


class TestNDBOpenIDStore(object):
    
    def setup_method(self, method):
        self.testbed = testbed.Testbed()
        self.testbed.activate()
        self.testbed.init_datastore_v3_stub()
        self.testbed.init_memcache_stub()
    
    
    def teardown_method(self, method):
        self.testbed.deactivate()
        
    
    def test_storeAssociation(self):
        """Tests the NDBOpenIDStore.storeAssociation(server_url, association) method."""
        
        # create association mock
        association = AssociationMock(handle='handle',
                                      serialized='serialized',
                                      issued=123,
                                      lifetime=60)
        
        server_url = 'server_url_abc'
        
        # store association
        NDBOpenIDStore.storeAssociation(server_url, association)
        
        # retrieve association
        key = ndb.Key('ServerUrl', server_url, NDBOpenIDStore, association.handle)
        entity = key.get()
        
        # check if entity exists
        assert entity is not None
        
        # check whether serialized match
        assert entity.serialized == association.serialize()
        
        # check whether expiration_date match
        issued = datetime.datetime.fromtimestamp(association.issued)
        lifetime = datetime.timedelta(0, association.lifetime)        
        expiration_date = issued + lifetime
        
        assert entity.expiration_date == expiration_date
    
    
    def test_remove_expired(self):
        """Tests the NDBOpenIDStore._delete_expired() method."""
        
        number_of_valid = 5
        number_of_expired = 5
        
        # populate datastore with valid associations
        for i in range(number_of_valid):
            url = 'url-{}'.format(i)
            
            association = AssociationMock(handle='handle_{}'.format(i),
                                          serialized='serialized_{}'.format(i),
                                          issued=int(time.time()),
                                          lifetime=3600)
            
            NDBOpenIDStore.storeAssociation(url, association)
        
        # check whether the valid ones are there
        assert NDBOpenIDStore.query().count() == number_of_valid
        
        
        # populate datastore with expired associations
        for i in range(number_of_valid, number_of_expired + number_of_valid):
            url = 'url-{}'.format(i)
            
            # create association mock beyond expiration
            association = AssociationMock(handle='handle_{}'.format(i),
                                          serialized='serialized_{}'.format(i),
                                          issued=int(time.time()) - 3600,
                                          lifetime=1000)
            
            NDBOpenIDStore.storeAssociation(url, association)
        
        # check whether the expired ones were added
        assert NDBOpenIDStore.query().count() == number_of_expired + number_of_valid
        
        # call the tested method
        NDBOpenIDStore._delete_expired()
        
        # get remaining
        remaining = NDBOpenIDStore.query().fetch()
        
        # check the number of remaining
        assert len(remaining) == number_of_valid
        
        # check whether all the remaining are valid
        for entity in remaining:
            assert entity.expiration_date >= datetime.datetime.now()
        
    