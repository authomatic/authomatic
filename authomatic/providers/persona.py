from google.appengine.api import users
from authomatic import providers
from authomatic.exceptions import FailureError
import logging
import authomatic.core as core
import authomatic.settings as settings

class MozillaPersona(providers.AuthenticationProvider):
    pass
