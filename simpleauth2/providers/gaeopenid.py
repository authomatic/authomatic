from google.appengine.api import users
import simpleauth2
import logging

class GAEOpenID(simpleauth2.providers.OpenIDBaseProvider):
    """OpenID provider based on google.appengine.api.users library."""
    
    def login(self, *args, **kwargs):
        """
        Launches the OpenID authentication procedure.
        
        Accepts oi_identifier optional parameter
        """
        
        super(GAEOpenID, self).login(*args, **kwargs)
        
        if self.phase == 0 and self.identifier:
            # redirect to google auth service
            self.adapter.redirect(users.create_login_url(dest_url=self.uri, federated_identity=self.identifier))            
            
            self._increase_phase()
        
        if self.phase == 1:
            
            self._reset_phase()
            
            user = users.get_current_user()
            
            if user:
                self._user = simpleauth2.User(user_id=user.federated_identity(),
                                              email=user.email(),
                                              gae_user=user)
            
                self.callback(simpleauth2.AuthEvent(self))
            else:
                self._finish(simpleauth2.AuthError.FAILURE)





