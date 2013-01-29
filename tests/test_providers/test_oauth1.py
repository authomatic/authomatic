from simpleauth2.providers import oauth1
import binascii
import hashlib
import hmac
import simpleauth2
import urllib
import urlparse


def create_signature(base_string, key):
    # Generate HMAC-SHA1 signature
    # http://oauth.net/core/1.0a/#rfc.section.9.2
    hashed = hmac.new(key, base_string, hashlib.sha1)
    return binascii.b2a_base64(hashed.digest())[:-1]


def get_signature(url):
    parsed = urlparse.urlparse(url)
    query = urlparse.parse_qs(parsed.query, True)
    return query.get('oauth_signature', [])[0]


class TestCreateUrl(object):
    
    def test_normalize_params(self):
        
        params = [('a', '1'),
                  ('c', 'hi there~wasup'),
                  ('f', '25'),
                  ('f', '50'),
                  ('f', 'a'),
                  ('z', 'p'),
                  ('z', 't')]
        
        normalized_qs = oauth1._normalize_params(params)
        
        assert normalized_qs == 'a=1&c=hi%20there~wasup&f=25&f=50&f=a&z=p&z=t'
    
    def test_create_url(self):
        
        method = 'GET'
        base = 'http://example.com/auth'
        callback = 'http://callback.com?param1=value1&param2=value2'
        consumer_key = 'abcdef'
        consumer_secret = 'ghijkl'
        nonce = '12345'