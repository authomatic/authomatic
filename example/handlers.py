from simpleauth2.extras import SessionRequestHandler
from webapp2_extras import sessions
import config
import pprint
import simpleauth2
import webapp2

class Home(SessionRequestHandler):
    def get(self):
        count = self.session.get('count') or 0
        self.session['count'] = count + 1
        self.response.write('HOME ' + str(count))

class Auth(SessionRequestHandler, simpleauth2.auth_mixin_factory(config.SERVICES)):
    def callback(self, event):
        
        user_info = event.get_user_info()
        
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
        
        
        self.response.write('<br /><br />')
        self.response.write(user_info.raw_user_info)