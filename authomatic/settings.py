"""
Global variables set up in Middleware.
"""

import logging

config = None
report_errors = None
prefix = prefix = None

#: :class:`int` The logging level treshold as specified in the standard Python
#: `logging library <http://docs.python.org/2/library/logging.html>`_.
#: If :literal:`None` or :literal:`False` there will be no logs. Default is ``logging.INFO``.
logging_level = logging.INFO