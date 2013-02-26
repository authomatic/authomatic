
from google.appengine.ext import testbed, ndb
from authomatic.extras.gae.openid import NDBOpenIDStore
import datetime
import pytest
import time

from openid.association import Association


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
        
        # create association
        association = Association(handle='handle',
                                  secret='secret',
                                  issued=int(time.time()),
                                  lifetime=3600,
                                  assoc_type='HMAC-SHA1')
        
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
        
        # check whether the original and deserialized associations match
        assert association == Association.deserialize(entity.serialized)
    
    
    def test_cleanupAssociations(self):
        """Tests the NDBOpenIDStore._delete_expired() method."""
        
        number_of_valid = 5
        number_of_expired = 5
        
        # populate datastore with valid associations
        for i in range(number_of_valid):
            url = 'url-{}'.format(i)
            
            association = Association(handle='handle_{}'.format(i),
                                      secret='secret',
                                      issued=int(time.time()),
                                      lifetime=3600,
                                      assoc_type='HMAC-SHA1')
            
            NDBOpenIDStore.storeAssociation(url, association)
        
        # check whether the valid ones are there
        assert NDBOpenIDStore.query().count() == number_of_valid
        
        
        # populate datastore with expired associations
        for i in range(number_of_valid, number_of_expired + number_of_valid):
            url = 'url-{}'.format(i)
            
            # create association mock beyond expiration
            association = Association(handle='handle_{}'.format(i),
                                      secret='secret',
                                      issued=int(time.time()) - 3600,
                                      lifetime=1000,
                                      assoc_type='HMAC-SHA1')
            
            NDBOpenIDStore.storeAssociation(url, association)
        
        # check whether the expired ones were added
        assert NDBOpenIDStore.query().count() == number_of_expired + number_of_valid
        
        # call the tested method
        removed = NDBOpenIDStore.cleanupAssociations()
        
        # check whether the method returned the correct number of deleted
        assert removed == number_of_expired
        
        # get remaining
        remaining = NDBOpenIDStore.query().fetch()
        
        # check the number of remaining
        assert len(remaining) == number_of_valid
        
        # check whether all the remaining are valid
        for entity in remaining:
            assert entity.expiration_date >= datetime.datetime.now()
        
        # call the tested method again
        removed = NDBOpenIDStore.cleanupAssociations()
        
        # removed should now be 0
        assert removed == 0
        
        # valid should still be there
        assert NDBOpenIDStore.query().count() == number_of_valid
    
    
    def test_getAssociation(self):
        
        # prepare associations for "url_a"
        url_a_associations = []
        
        # add some valid associations with ascending issue times and descending expiration
        # so the most recently issued is url_b_associations[4]
        # and the longest valid is url_b_associations[0]
        url_a_associations += [Association(handle='handle-{}'.format(i),
                                           secret='secret',
                                           issued=int(time.time()) + i,
                                           lifetime=3600 - i * 10,
                                           assoc_type='HMAC-SHA1') for i in range(5)]
        
        # add some expired associations
        url_a_associations += [Association(handle='handle-{}'.format(i),
                                           secret='secret',
                                           issued=int(time.time()) - 3600,
                                           lifetime=1,
                                           assoc_type='HMAC-SHA1') for i in range(5, 10)]
        
        # store them
        for assoc in url_a_associations:
            NDBOpenIDStore.storeAssociation('url_a', assoc)
        
        
        # prepare associations for "url_b"
        url_b_associations = []
        
        # add some valid associations with ascending issue times and descending expiration
        # so the most recently issued is url_b_associations[4]
        # and the longest valid is url_b_associations[0]
        url_b_associations += [Association(handle='handle-{}'.format(i),
                                           secret='secret',
                                           issued=int(time.time()) + i,
                                           lifetime=3600 - i * 10,
                                           assoc_type='HMAC-SHA1') for i in range(5)]
        
        # add some expired associations
        url_b_associations += [Association(handle='handle-{}'.format(i),
                                           secret='secret',
                                           issued=int(time.time()) - 3600,
                                           lifetime=1,
                                           assoc_type='HMAC-SHA1') for i in range(5, 10)]
        
        # store them under "url_a"
        for assoc in url_b_associations:
            NDBOpenIDStore.storeAssociation('url_b', assoc)
        
        # check whether they are all there
        assert len(url_a_associations + url_b_associations) == NDBOpenIDStore.query().count()
        
        
        # call the tested method
        
        # test for "url_a"
        
        # get a valid association with url and handle
        association = NDBOpenIDStore.getAssociation('url_a', 'handle-3')
        assert association == url_a_associations[3]
        
        # get a valid association with url only
        # should return the most recent association
        association = NDBOpenIDStore.getAssociation('url_a')
        assert association == url_a_associations[4]
        
        
        # test for "url_b"
        
        # get a valid association with url and handle
        association = NDBOpenIDStore.getAssociation('url_b', 'handle-2')
        assert association == url_b_associations[2]
        
        # get a valid association with url only
        # should return the most recent association
        association = NDBOpenIDStore.getAssociation('url_b')
        assert association == url_b_associations[4]
        
        
        # test for non existent url
        association = NDBOpenIDStore.getAssociation('non_existent_url')
        assert association is None
    
    
    def test_removeAssociation(self):
        
        # create and store some associations
        associations = []
        
        for i in range(3):
            assoc = Association(handle='handle-{}'.format(i),
                                secret='secret',
                                issued=int(time.time()),
                                lifetime=3600,
                                assoc_type='HMAC-SHA1')
            associations.append(assoc)
            NDBOpenIDStore.storeAssociation('server_url', assoc)
        
        # remove existing association
        removed = NDBOpenIDStore.removeAssociation('server_url', 'handle-1')
        
        # check whether the method returned True
        assert removed is True
        
        # check whether there is one less association in the datastore
        assert NDBOpenIDStore.query().count() == 2
        
        # check whether the right association was deleted
        assert NDBOpenIDStore.getAssociation('server_url', 'handle-1') is None
        
        # check whether the remaining are there
        assert NDBOpenIDStore.getAssociation('server_url', 'handle-0') == associations[0]
        assert NDBOpenIDStore.getAssociation('server_url', 'handle-2') == associations[2]
    
    
    def test_useNonce(self):
        nonce = ('server_url', 123456789, 'salt')
        
        # check whether the method returns True with fresh nonce
        assert NDBOpenIDStore.useNonce(*nonce) is True
        
        # check whether the method returns False with already used nonce
        assert NDBOpenIDStore.useNonce(*nonce) is False
        
        
        # check again with different nonce
        nonce = ('server_url_b', 987654321, 'sugar')
        
        # check whether the method returns True with fresh nonce
        assert NDBOpenIDStore.useNonce(*nonce) is True
        
        # check whether the method returns False with already used nonce
        assert NDBOpenIDStore.useNonce(*nonce) is False
    
    
    def test_cleanupNonces(self):
        
        # use valid and expired nonces
        for i in range(10):
            # first 5 are valid rest is expired
            timestamp = time.time() if i < 5 else i
            salt = 'valid' if i < 5 else 'expired'
            NDBOpenIDStore.useNonce('server_url', timestamp, salt)
        
        query = NDBOpenIDStore.query()
        
        # check whether all nonces are in the datastore
        assert query.count() == 10
                        
        # call the tested method
        deleted = NDBOpenIDStore.cleanupNonces()
        
        # check whether the returned value coresponds with the number of deleted nonces
        assert deleted == 5
        
        # check whether there there are 5 less nonces
        assert query.count() == 5
        
        # call the tested method again
        deleted = NDBOpenIDStore.cleanupNonces()
        # the returned value should now be 0
        assert deleted == 0
        
        # check whether there still are 5 valid nonces
        assert query.count() == 5









        
    