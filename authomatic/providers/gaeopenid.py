"""
Google App Engine OpenID Providers
----------------------------------

This module provides `OpenID <http://openid.net/>`_ :doc:`providers` based on
`Google App Engine Users API <https://developers.google.com/appengine/docs/python/users/>`_ library.

.. note::

    When using these providers the :class:`user <.core.User>` object will always have only the
    :attr:`user_id <.core.User.user_id>`,
    :attr:`email <.core.User.email>`,
    :attr:`gae_user <.core.User.gae_user>`
    attributes populated with data.
    Moreover the :attr:`user_id <.core.User.user_id>` will always be empty on the
    `Development Server <https://developers.google.com/appengine/docs/python/tools/devserver>`_.

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

__all__ = ['GAEOpenID', 'Yahoo', 'Google']

class GAEOpenID(providers.AuthenticationProvider):
    """
    OpenID provider based on the
    `Google App Engine Users API <https://developers.google.com/appengine/docs/python/users/>`_ library.
    
    .. automethod:: __init__(*args, identifier='')
        
        Accepts additional keyword argument :data:`identifier`, the *OpenID claimed identity* to authenticate.
        
    """
    
    @providers.login_decorator
    def login(self):
        """Launches the OpenID authentication procedure."""
        
        if self.identifier:
            #===================================================================
            # Phase 1 before redirect.
            #===================================================================
            self._log(logging.INFO, 'Starting OpenID authentication procedure.')
            
            url = users.create_login_url(dest_url=self.adapter.url, federated_identity=self.identifier)
            
            self._log(logging.INFO, 'Redirecting user to {}.'.format(url))
            
            self.adapter.redirect(url)
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
                                     user_id=user.federated_identity(),
                                     email=user.email(),
                                     gae_user=user)
                
                #===============================================================
                # We're done
                #===============================================================
            else:
                raise FailureError('Unable to authenticate user id!')

class Yahoo(GAEOpenID):
    """
    :class:`.GAEOpenID` provider with the :attr:`.identifier` predefined to ``"me.yahoo.com"``.
    """
    
    identifier = 'me.yahoo.com'

class Google(GAEOpenID):
    """
    :class:`.GAEOpenID` provider with the :attr:`.identifier` predefined to
    ``"https://www.google.com/accounts/o8/id"``.
    """
    
    identifier = 'https://www.google.com/accounts/o8/id'
