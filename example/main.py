import config
import logging
import simpleauth2
import webapp2


class Home(webapp2.RequestHandler):
    def get(self):
        self.response.write('Home<br />')
        

class Login(webapp2.RequestHandler):
    
    def get(self, provider_name):
        
        simpleauth2.login(provider_name, self.callback, self, session_secret='abcd', providers_config=config.PROVIDERS)
    
    def callback(self, event):
                
        # fetch user info asynchronously
        event.provider.user_info_request.fetch()
               
        self.response.write('<br /><br />')
        self.response.write('<a href="/auth/facebook">Facebook</a><br />')
        self.response.write('<a href="/auth/google">Google</a><br />')
        self.response.write('<a href="/auth/windows_live">Windows Live</a><br />')
        self.response.write('<a href="/auth/twitter">Twitter</a><br />')
        
        self.response.write('<br /><br />')
        self.response.write('Credentials:<br /><br />')
        
        # credentials
        for k, v in event.credentials.__dict__.items():
            self.response.write('{}: {}<br />'.format(k, v))        
        
        self.response.write('<br /><br />')
        self.response.write('User Info:<br /><br />')
        
        # get result of asynchronous call
        user = event.provider.user_info_request.fetch().get_result()
        
        for k, v in user.__dict__.items():
            if k != 'raw_user_info':
                self.response.write('{}: {}<br />'.format(k, v))
        
        self.response.write('<br /><br />')
        self.response.write('Raw User Info:<br /><br />')
        self.response.write(user.raw_user_info)

# routes must be named
ROUTES = [webapp2.Route(r'/auth/<:.*>', Login, 'auth'),
          webapp2.Route(r'/', Home)]

app = webapp2.WSGIApplication(ROUTES, debug=True)