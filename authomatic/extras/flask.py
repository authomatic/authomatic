# -*- coding: utf-8 -*-
"""
|flask| Extras
--------------

Utilities you can use when using this library with the |flask|_ framework.

Thanks to `Mark Steve Samson <http://marksteve.com>`_.
"""

from __future__ import absolute_import
from functools import wraps

from authomatic.adapters import WerkzeugAdapter
from authomatic import Authomatic
from flask import make_response, request, session


class FlaskAuthomatic(Authomatic):
    """
    Flask Plugin for authomatic support.
    """

    result = None

    def login(self, *login_args, **login_kwargs):
        """
        Decorator for Flask view functions.
        """

        def decorator(f):
            @wraps(f)
            def decorated(*args, **kwargs):
                self.response = make_response()
                adapter = WerkzeugAdapter(request, self.response)
                login_kwargs.setdefault('session', session)
                login_kwargs.setdefault('session_saver', self.session_saver)
                self.result = super(FlaskAuthomatic, self).login(
                    adapter,
                    *login_args,
                    **login_kwargs)
                return f(*args, **kwargs)
            return decorated
        return decorator

    def session_saver(self):
        session.modified = True
