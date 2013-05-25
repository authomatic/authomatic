from functools import wraps

from authomatic.adapters import WerkzeugAdapter
from flask import make_response, request, session
import authomatic


class FlaskAuthomatic(object):
    """
    Flask Plugin for authomatic support
    """

    result = None

    def __init__(self, *args, **kwargs):
        if args or kwargs:
            self.setup(*args, **kwargs)

    def setup(self, *args, **kwargs):
        authomatic.setup(*args, **kwargs)

    def login(self, *login_args, **login_kwargs):
        """
        Decorator for Flask view functions
        """
        def decorator(f):
            @wraps(f)
            def decorated(*args, **kwargs):
                adapter = WerkzeugAdapter(request, make_response())
                login_kwargs.setdefault('session', session)
                login_kwargs.setdefault('session_saver', self.session_saver)
                self.result = authomatic.login(adapter, *login_args,
                                               **login_kwargs)
                self.response = adapter.response
                return f(*args, **kwargs)
            return decorated
        return decorator

    def session_saver(self):
        session.modified = True
