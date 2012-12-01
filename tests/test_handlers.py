import simpleauth2
import pytest
import webapp2

class TestLoginMixin():
    
    def test_auth_mixin_factory(self):
        """Tests the auth_mixin_factory function"""
        
        class Handler(simpleauth2.auth_mixin_factory('abcdefg')):
            pass
        
        handler = Handler()
        
        assert handler.config == 'abcdefg'