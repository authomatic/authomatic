from google.appengine.api import urlfetch
from urllib import urlencode
import logging
import oauth2 as oauth1
import urlparse

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

class FetchResult(object):
    """
    Provides unified interface to results of different http request types
    
    The interface resembles the google.appengine.api.urlfetch.fetch()
    """
    def __init__(self, response):
        
        if type(response) == urlfetch._URLFetchResult:
            # if request returned by google.appengine.api.urlfetch.fetch()
            self.content = response.content
            self.status_code = int(response.status_code)
            self.headers = response.headers
            self.final_url = response.final_url
            
        elif type(response) == tuple:
            # if request returned by oauth2.Client.request()
            self.headers = response[0]
            self.content = response[1]
            self.status_code = int(self.headers['status'])
            self.final_url = None
        
        self.data = json.loads(self.content)

def create_oauth1_url(base, access_token, access_token_secret, service_ID, secret):
    
    token = oauth1.Token(access_token, access_token_secret)
    consumer = oauth1.Consumer(service_ID, secret)
    client = oauth1.Client(consumer, token)
    
    request = oauth1.Request.from_consumer_and_token(consumer, token)
    request.url = base
    request.sign_request(client.method, consumer, token)
    
    logging.info('request = {}'.format(request))
    
    params = urlencode(request)
    
    return base + '?' + params

def create_oauth2_url(base, access_token):
    
    return base + '?' + urlencode(dict(access_token=access_token))

def fetch(service_type, url, access_token, method='GET', access_token_secret=None, service_ID=None, secret=None):
    """
    Common interface to oauth2_fetch() and oauth1_fetch()
    """
    
    if service_type == 'OAuth2':
        url = create_oauth2_url(url, access_token)
    elif service_type == 'OAuth1':
        url = create_oauth1_url(url, access_token, access_token_secret, service_ID, secret)
    
    result = urlfetch.fetch(url, method=method)
    
    return FetchResult(result)

def call_async(calls, callback):
    
    rpc = urlfetch.create_rpc()
    
    rpc.callback = lambda: None
    
    event = None
    callback(event)






