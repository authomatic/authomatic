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