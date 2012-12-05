import config
import simpleauth2
import webapp2
from simpleauth2 import services, utils
import logging

ConfiguredAuthMixin = simpleauth2.auth_mixin_factory(config.SERVICES, config.SESSION)

class Login(webapp2.RequestHandler, ConfiguredAuthMixin):
    
    def get(self, service_name):
        self.simpleauth2.login(service_name, self.callback)
    
    def callback(self, event):
        
        
        user_info = event.service.get_user_info()
        
        self.response.write('Type: {}<br /><br />'.format(event.service.type))
        self.response.write('Name: {}<br /><br />'.format(event.service.service_name))
        
        self.response.write(event.access_token)
        self.response.write('<br /><br />')
        self.response.write(event.expires)
        self.response.write('<br /><br />')
        
        for k, v in user_info.__dict__.items():
            if k != 'raw_user_info':
                self.response.write('{}: {}<br />'.format(k, v))
                
        self.response.write('<br /><br />')
        self.response.write('<a href="/auth/facebook">Facebook</a><br />')
        self.response.write('<a href="/auth/google">Google</a><br />')
        self.response.write('<a href="/auth/windows_live">Windows Live</a><br />')
        self.response.write('<a href="/auth/twitter">Twitter</a><br />')
        
        # if Facebook
        if type(event.service) == simpleauth2.services.Facebook:
            
            self.response.write('Its Facebook<br /><br />')
            
            # fetch service api throug event without access token
            response = event.service.fetch('https://graph.facebook.com/me/music')
            self.response.write('Music:<br /><br />')            
            self.response.write(response.data)
            self.response.write('<br /><br />')
            
            
            logging.info('Response.status_code = {}'.format(response.status_code))
            logging.info('Response.status_code type = {}'.format(type(response.status_code)))
            logging.info('Response.headers = {}'.format(response.headers))
            logging.info('Response.final_url = {}'.format(response.final_url))
        
        
        # if Twitter
        if type(event.service) == simpleauth2.services.Twitter:
            
            self.response.write('Its Twitter<br /><br />')
            
            # fetch service api throug event without access token
            response = event.service.fetch('https://api.twitter.com/1.1/statuses/user_timeline.json')
            
            self.response.write('Location: {}<br /><br />'.format(response.headers.get('content-location')))
            
            logging.info('Response.status_code = {}'.format(response.status_code))
            logging.info('Response.status_code type = {}'.format(type(response.status_code)))
            logging.info('Response.headers = {}'.format(response.headers))
            logging.info('Response.final_url = {}'.format(response.final_url))
            
            self.response.write('Statuses:<br /><br />')            
            self.response.write(response.data)
            self.response.write('<br /><br />')
        
        self.response.write('<br /><br />')
        self.response.write(user_info.raw_user_info)

# routes must be named
ROUTES = [webapp2.Route(r'/auth/<:.*>', Login, 'auth')]

app = webapp2.WSGIApplication(ROUTES, debug=True)