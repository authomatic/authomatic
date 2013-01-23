from google.appengine.api import users
from simpleauth2.providers import BaseProvider
import logging

class GAEOpenID(BaseProvider):
    
    def login(self):
        
        logging.info('GAEOpenID')
        
        if self.phase == 0:
            
            self._increase_phase()
            
            # get Open ID identifier
            identifier = self.urls[0] or self.adapter.get_request_param('id')
            
            target_url = users.create_login_url(dest_url=self.uri, federated_identity=identifier)
            
            self.adapter.redirect(target_url)            
            
        
        if self.phase == 1:
            
            self._reset_phase()
            
            user = users.get_current_user()
            
            logging.info('user.federated_identity() = {}'.format(user.federated_identity()))
            logging.info('user.nickname() = {}'.format(user.nickname()))
            logging.info('user.email() = {}'.format(user.email()))
            
            
