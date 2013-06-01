# -*- coding: utf-8 -*-
"""
This is the only interface that you should ever need to get a **user** logged in, get
**his/her** info and credentials, deserialize the credentials
and access **his/her protected resources**.

.. autosummary::
    :nosignatures:
    
    authomatic.setup
    authomatic.login
    authomatic.provider_id
    authomatic.access
    authomatic.async_access
    authomatic.credentials
    authomatic.request_elements
    authomatic.backend

"""

from core import Authomatic, setup, login, provider_id, access, async_access, credentials, request_elements, backend
