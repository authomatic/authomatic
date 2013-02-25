"""
Global variables set up in Middleware.
"""

import logging

config = None
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