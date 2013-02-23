"""
Google App Engine OpenID Providers
----------------------------------

Providers which implement the |openid|_ protocol based on the |gae_users_api|_.

.. note::

    When using the :class:`GAEOpenID` provider, the :class:`user <.core.User>` object
    will always have only the
    :attr:`user_id <.core.User.user_id>`,
    :attr:`email <.core.User.email>`,
    :attr:`gae_user <.core.User.gae_user>`
    attributes populated with data.
    Moreover the :attr:`user_id <.core.User.user_id>` will always be empty on the
    `GAE Development Server <https://developers.google.com/appengine/docs/python/tools/devserver>`_.

.. autosummary::
    
    GAEOpenID
    Yahoo
    Google 

"""

from google.appengine.api import users
from authomatic import providers
from authomatic.exceptions import FailureError
import logging
import authomatic.core as core
import authomatic.settings as settings

__all__ = ['GAEOpenID', 'Yahoo', 'Google']

class GAEOpenID(providers.AuthenticationProvider):
    """
    |openid|_ provider based on the |gae_users_api|_.
    
    Accepts additional keyword arguments inherited from :class:`.AuthenticationProvider`.
    """
    
    @providers.login_decorator
    def login(self):
        """Launches the OpenID authentication procedure."""
        
        if core.mw.params.get(self.identifier_param):
            #===================================================================
            # Phase 1 before redirect.
            #===================================================================
            self._log(logging.INFO, 'Starting OpenID authentication procedure.')
            
            url = users.create_login_url(dest_url=core.mw.url, federated_identity=self.identifier)
            
            self._log(logging.INFO, 'Redirecting user to {}.'.format(url))
            
            core.mw.redirect(url)
        else:
            #===================================================================
            # Phase 2 after redirect.
            #===================================================================
            
            self._log(logging.INFO, 'Continuing OpenID authentication procedure after redirect.')
            
            user = users.get_current_user()
            
            if user:
                self._log(logging.INFO, 'Authentication successful.')
                self._log(logging.INFO, 'Creating user.')
                self.user = core.User(self,
                                     id=user.federated_identity(),
                                     email=user.email(),
                                     gae_user=user)
                
                #===============================================================
                # We're done
                #===============================================================
            else:
                raise FailureError('Unable to authenticate identifier "{}"!'.format(self.identifier))

class Yahoo(GAEOpenID):
    """
    :class:`.GAEOpenID` provider with the :attr:`.identifier` predefined to ``"me.yahoo.com"``.
    """
    
    identifier = 'me.yahoo.com'

class Google(GAEOpenID):
    """
    :class:`.GAEOpenID` provider with the :attr:`.identifier` predefined to ``"https://www.google.com/accounts/o8/id"``.
    """
    
    identifier = 'https://www.google.com/accounts/o8/id'
