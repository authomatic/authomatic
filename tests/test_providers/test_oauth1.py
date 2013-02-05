from authomatic.providers import oauth1
import binascii
import hashlib
import hmac
import authomatic
import urllib
import urlparse
from urllib import urlencode


def create_signature(base_string, key):
    # Generate HMAC-SHA1 signature
    # http://oauth.net/core/1.0a/#rfc.section.9.2
    hashed = hmac.new(key, base_string, hashlib.sha1)
    return binascii.b2a_base64(hashed.digest())[:-1]


def get_signature(url):
    parsed = urlparse.urlparse(url)
    query = urlparse.parse_qs(parsed.query, True)
    return query.get('oauth_signature', [])[0]


class SignatureSetupTeardown(object):
    def setup_method(self, method):
        
        self.consumer_secret = 'consumer-secret'
        self.token_secret = 'token-secret'
        
        self.method = 'GET'
        self.base = 'http://example.com/path'
        
        self.params = [('a', '1'),
                  ('c', 'hi there~wasup'),
                  ('f', '25'),
                  ('f', '50'),
                  ('f', 'a'),
                  ('z', 'p'),
                  ('z', 't'),
                  ('realm', 'realm value'),
                  ('oauth_signature', 'oauth_signature value')]
        
        self.url = self.base + '?' + urllib.urlencode(self.params)


class TestCreateSignature(SignatureSetupTeardown):
    
    def test__normalize_params(self):
        
        normalized_qs = oauth1._normalize_params(self.params)
        
        assert normalized_qs == 'a=1&c=hi%20there~wasup&f=25&f=50&f=a&z=p&z=t'
    
    
    def test__split_url(self):
        
        url = 'http://example.com/path?a=1&c=hi%20there~wasup&f=25&f=50&f=a&z=p&z=t'
        
        
        base, params = oauth1._split_url(url)
        
        assert base == 'http://example.com/path'
        
        sorted_extracted_params = [i for i in params].sort()
        sorted_params = [i for i in self.params].sort()
        
        assert sorted_extracted_params == sorted_params
    
    
    def test__create_base_string(self):
        
        url = ''.join([self.base,
                       '?',
                       'realm=realm_value&',
                       'oauth_signature=oauth_signature_value&',
                       'c=c_value&',
                       'a=a_value&',
                       '10=10_value&',
                       '11=11_value&',
                       'b=b_value&',
                       'x=x_value&',
                       '1=1_value',])
        
        normalized_qs = '1=1_value&10=10_value&11=11_value&a=a_value&b=b_value&c=c_value&x=x_value'
        
        desired_base_string = '&'.join([authomatic.escape(self.method),
                                        authomatic.escape('http://example.com/path'),
                                        authomatic.escape(normalized_qs)])
        
        params = [('realm', 'realm_value'),
                  ('oauth_signature', 'oauth_signature_value'),
                  ('c', 'c_value'),
                  ('a', 'a_value'),
                  ('10', '10_value'),
                  ('11', '11_value'),
                  ('b', 'b_value'),
                  ('x', 'x_value'),
                  ('1', '1_value')]
        
        assert desired_base_string == oauth1._create_base_string(self.method, self.base, params)


class TestHMACSHA1Generator(SignatureSetupTeardown):
    
    def test__create_key(self):
        
        consumer_secret = 'cs'
        token_secret = 'ts'
        
        desired_key = authomatic.escape(consumer_secret) + '&' + authomatic.escape(token_secret)
        
        assert oauth1.HMACSHA1Generator._create_key(consumer_secret, token_secret) == desired_key
    
    
    def test__create_signature(self):

        params2 = [i for i in self.params]
        params2.reverse()
        
        signature1 = oauth1.HMACSHA1Generator.create_signature(self.method, self.base,
                                                                self.params, self.consumer_secret,
                                                                self.token_secret)
        
        signature2 = oauth1.HMACSHA1Generator.create_signature(self.method, self.base,
                                                                params2, self.consumer_secret,
                                                                self.token_secret)
        
        assert signature1 == signature2


