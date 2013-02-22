import datetime
import httplib
import threading
import time
import urlparse
import urllib2

#def resolve_http_redirect(url, depth=0):
#    if depth > 10:
#        raise Exception("Redirected "+depth+" times, giving up.")
#    o = urlparse.urlparse(url,allow_fragments=True)
#    conn = httplib.HTTPConnection(o.netloc)
#    path = o.path
#    if o.query:
#        path +='?'+o.query
#    conn.request("HEAD", path)
#    res = conn.getresponse()
#    headers = dict(res.getheaders())
#    if headers.has_key('location') and headers['location'] != url:
#        return resolve_http_redirect(headers['location'], depth+1)
#    else:
#        return url

def new_fetch(url, body=None, method='GET', headers={}, max_redirects=4):
    
    print 'Fetching url = {}'.format(url)
    print 'remaining redirects = {}'.format(max_redirects)
    
    scheme, host, path, query, fragment = urlparse.urlsplit(url)
    
    connection = httplib.HTTPConnection(host)
    
    p = urlparse.urlunsplit((None, None, path, query, None))
    
    try:
        connection.request(method, p, body, headers)
    except Exception as e:
        print 'Could not connect! Error: {}'.format(e.message)
    
    response = connection.getresponse()
    
    location = response.getheader('Location')
    
    if response.status in (300, 301, 302, 303, 307) and location:
        if location == url:
            print 'Loop redirect to = {}'.format(location)
            return
        elif max_redirects > 0:
            print 'Redirecting to = {}'.format(location)
            response = new_fetch(location, body, method, headers, max_redirects=max_redirects - 1)
        else:
            print 'Max redirects reached!'
            return
    else:
        print 'Got response from url = {}'.format(url)
    return response


class MultiMethodRequest(urllib2.Request):
    def __init__(self, method='GET', *args, **kwargs):
        urllib2.Request.__init__(self, *args, **kwargs)
        self._method = method
    
    def get_method(self):
        if self._method:
            return self._method
        else:
            return urllib2.Request.get_method(self)


def fetch2(url, body=None, method='GET', headers={}):
    print 'Fetching url = {}'.format(url)
#    request = MultiMethodRequest(method, url, body, headers)
    
    request = urllib2.Request(url, body, headers)
    request.get_method = lambda: 'DELETE'
    
    res = urllib2.urlopen(request)
    print 'Got response from url = {}'.format(url)
    return res


class Future(threading.Thread):
    """
    http://code.activestate.com/recipes/84317-easy-threading-with-futures/
    """
    
    def __init__(self, *args, **kwargs):
        super(Future, self).__init__()
        
        self.args = args
        self.kwargs = kwargs
        
        self.result = None
    
    def run(self):
        self.result = fetch2(*self.args, **self.kwargs)
    
    def get_result(self):
        self.join()
        return self.result


def async_fetch(*args, **kwargs):
    af = Future(*args, **kwargs)
    af.start()
    return af


headers = {
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
    'Accept-Charset': 'ISO-8859-1,utf-8;q=0.7,*;q=0.3',
    'Accept-Encoding': 'gzip,deflate,sdch',
    'Accept-Language': 'en-US,en;q=0.8',
    'Cache-Control': 'max-age=0',
    'Connection': 'keep-alive',
    'Host': 'www.hillbridges.sk',
    'User-Agent': 'Mozilla/5.0 (X11; Linux i686) AppleWebKit/535.19 (KHTML, like Gecko) Ubuntu/12.04 Chromium/18.0.1025.168 Chrome/18.0.1025.168 Safari/535.19',
    
}

resp = new_fetch('https://graph.facebook.com/oauth/access_token')

print resp.status
print resp.read()
#print resp.getheader('Location')

#print fetch2('https://graph.facebook.com/737583375?fields=cover', method='PUT').read()

#f1 = async_fetch('https://graph.facebook.com/737583375?fields=id,name')
#f2 = async_fetch('https://graph.facebook.com/737583375?fields=cover', method='PUT')
#f3 = async_fetch('https://graph.facebook.com/737583375?fields=cover')
#
#print 'Doing stuff...'
#
#r1 = f1.get_result()
#r2 = f2.get_result()
#r3 = f3.get_result()
#
#print 'result:\n\n1 = {} \n\n2 = {} \n\n3 = {}'.format(r1.read(), r2.read(), r3.read())




