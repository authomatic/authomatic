from __future__ import absolute_import

from functools import wraps

from authomatic.adapters import WerkzeugAdapter
from flask import make_response, request, session
from authomatic import Authomatic


class FlaskAuthomatic(Authomatic):
    """
    Flask Plugin for authomatic support
    """

    result = None

    def login(self, *login_args, **login_kwargs):
        """
        Decorator for Flask view functions
        """
        def decorator(f):
            @wraps(f)
            def decorated(*args, **kwargs):
                self.response = make_response()
                adapter = WerkzeugAdapter(request, self.response)
                login_kwargs.setdefault('session', session)
                login_kwargs.setdefault('session_saver', self.session_saver)
                self.result = super(FlaskAuthomatic, self).login(adapter, *login_args, **login_kwargs)
                return f(*args, **kwargs)
            return decorated
        return decorator

    def session_saver(self):
        session.modified = True
