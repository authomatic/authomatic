"""
Global variables set up in Middleware.
"""

import logging

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

#: Maximum allowed age of :class:`.Session` kookie nonce in seconds.
session_max_age = 600

#: :class:`int` The logging level treshold as specified in the standard Python
#: `logging library <http://docs.python.org/2/library/logging.html>`_.
logging_level = logging.INFO