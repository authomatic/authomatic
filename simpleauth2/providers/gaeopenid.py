from google.appengine.api import users
from simpleauth2 import providers
from simpleauth2.exceptions import FailureError
import logging
import simpleauth2

class GAEOpenID(simpleauth2.providers.AuthenticationProvider):
    """OpenID provider based on google.appengine.api.users library."""
    
    @providers._login_decorator
    def login(self, *args, **kwargs):
        """
        Launches the OpenID authentication procedure.
        
        Accepts oi_identifier optional parameter
        """
        
        super(GAEOpenID, self).login(*args, **kwargs)
        
        if self.identifier:
            url = users.create_login_url(dest_url=self.uri, federated_identity=self.identifier)
            self.adapter.redirect(url)
        else:
            # returned from redirect or somebody requested without identifier
            user = users.get_current_user()
            if user:
                self._user = simpleauth2.User(user_id=user.federated_identity(),
                                              email=user.email(),
                                              gae_user=user)
                # We're done
            else:
                raise FailureError('Unable to verify user id!')


