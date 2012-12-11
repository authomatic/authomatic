
import config
import logging
import simpleauth2
import webapp2

class Login(webapp2.RequestHandler):
    
    def get(self, provider_name):
        
        simpleauth2.authenticate(provider_name, self.callback, self, config.PROVIDERS, session_secret='abcd')
    
    def callback(self, event):
                
        # fetch user info asynchronously
        event.provider.user_info_request.fetch()
               
                        
        self.response.write('<br /><br />')
        self.response.write('<a href="/auth/facebook">Facebook</a><br />')
        self.response.write('<a href="/auth/google">Google</a><br />')
        self.response.write('<a href="/auth/windows_live">Windows Live</a><br />')
        self.response.write('<a href="/auth/twitter">Twitter</a><br />')
        
        
        # get result of asynchronous call
        user_info = event.provider.user_info_request.fetch().get_result()
        
        for k, v in user_info.__dict__.items():
            if k != 'raw_user_info':
                self.response.write('{}: {}<br />'.format(k, v))

# routes must be named
ROUTES = [webapp2.Route(r'/auth/<:.*>', Login, 'auth')]

app = webapp2.WSGIApplication(ROUTES, debug=True)