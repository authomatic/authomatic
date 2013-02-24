"""
This is the only interface that you should ever need to get **user info** and **credentials**
from a **provider** and to make asynchronous calls to **protected resources** of the **user**.
"""

from core import login, provider_id, access, credentials
from core import setup_middleware as middleware
import settings

