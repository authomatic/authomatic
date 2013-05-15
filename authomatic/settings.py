# -*- coding: utf-8 -*-
"""
Global variables used throughout the library, set up in Middleware.
"""

import logging

#: The :doc:`config`.
config = None

#: A secret string that will be used as the key for signing :class:`.Session` cookie and
#: as a salt by *CSRF* token generation.
secret = ''

#: If ``True`` traceback of exceptions will be written to response.
debug = False

#: If ``True`` exceptions encountered during the **login procedure**
#: will be caught and reported in the :attr:`.LoginResult.error` attribute.
report_errors = None

#: Prefix used as the :class:`.Session` cookie name and
#: by which all logs will be prefixed.
prefix = prefix = None

#: If ``True`` the :class:`.Session` cookie will be saved wit ``Secure`` attribute.
secure_cookie = None

#: Maximum allowed age of :class:`.Session` cookie nonce in seconds.
session_max_age = 600

#: :class:`int` The logging level threshold as specified in the standard Python
#: `logging library <http://docs.python.org/2/library/logging.html>`_.
logging_level = logging.INFO

fetch_headers = {}
