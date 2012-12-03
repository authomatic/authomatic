import config
import simpleauth2
import webapp2

ConfiguredAuthMixin = simpleauth2.auth_mixin_factory(config.SERVICES, config.SESSION)

class Login(webapp2.RequestHandler, ConfiguredAuthMixin):
    
    def get(self, service_name):
        self.simpleauth2.login(service_name, self.callback)
    
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

# routes must be named
ROUTES = [webapp2.Route(r'/auth/<:.*>', Login, 'auth')]

app = webapp2.WSGIApplication(ROUTES, debug=True)