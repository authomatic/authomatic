from google.appengine.api import urlfetch
from urllib import urlencode
import urlparse
import oauth2 as oauth1

# taken from anyjson.py
try:
    import simplejson as json
except ImportError: # pragma: no cover
    try:
        # Try to import from django, should work on App Engine
        from django.utils import simplejson as json
    except ImportError:
        # Should work for Python2.6 and higher.
        import json

def json_parser(body):
    return json.loads(body)

def query_string_parser(body):
    res = dict(urlparse.parse_qsl(body))
    if not res:
        res = json_parser(body)
    return res

def fetch(service_type, url, access_token, *args, **kwargs):
    #TODO: Allow for http method argument
    if service_type == 'OAuth2':
        return oauth2_fetch(url, access_token)
    elif service_type == 'OAuth1':
        return oauth1_fetch(url, access_token, *args, **kwargs)

def oauth2_fetch(url, access_token):
    # construct url
    url = url + '?' + urlencode(dict(access_token=access_token))
    
    # fetch and decode response
    return json.loads(urlfetch.fetch(url).content)

def oauth1_fetch(url, access_token, access_token_secret, service_ID, secret):
    
    token = oauth1.Token(access_token, access_token_secret)
    consumer = oauth1.Consumer(service_ID, secret)
    client = oauth1.Client(consumer, token)
    
    content = client.request(url)[1]
    
    return json.loads(content)