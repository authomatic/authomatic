# -*- coding: utf-8 -*-
"""
This is the only interface that you should ever need to get a **user** logged in, get
**his/her** info and credentials, deserialize the credentials
and access **his/her protected resources**.
"""

from core import setup, login, provider_id, access, async_access, credentials, request_elements, \
    json_endpoint
import settings
