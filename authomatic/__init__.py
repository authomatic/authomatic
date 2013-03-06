# -*- coding: utf-8 -*-
"""
This is the only interface that you should ever need to get a **user** logged in, get
**his/her** info and credentials, deserialize the credentials
and access **his/her protected resources**.

.. autofunction:: middleware(app, config, secret, *args, **kwargs)

"""

from core import login, provider_id, access, async_access, credentials, \
    setup_middleware as middleware
import settings
