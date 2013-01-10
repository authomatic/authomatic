from simpleauth2 import Credentials, Request
from simpleauth2.adapters.gae_webapp2 import GAEWebapp2Adapter
import config
import logging
import simpleauth2
import sys
import webapp2

class Home(webapp2.RequestHandler):
    def get(self):
        self.response.write('Home<br />')
        

class Login(webapp2.RequestHandler):
    
    def get(self, provider_name):
        
        self.adapter = GAEWebapp2Adapter(handler=self,
                                    providers_config=config.PROVIDERS,
                                    session_secret='abcd')
        
        simpleauth2.login(self.adapter, provider_name, self.callback)
    
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
        
        serialized = event.credentials.serialize()
        
        deserialized = Credentials.from_serialized(self.adapter, serialized)
        
        self.response.write('<br /><br />')
        self.response.write('Serialized:<br />{}<br /><br />'.format(serialized)) 
        self.response.write('Serialized size:<br />{} B<br /><br />'.format(sys.getsizeof(serialized)))        
        
        # deserialized credentials
        for k, v in deserialized.__dict__.items():
            self.response.write('{}: {}<br />'.format(k, v)) 
        
        
        self.response.write('<br /><br />')
        self.response.write('User Info:<br /><br />')
        
        # fetch user info request the easy way
        user_rpc = event.provider.user_info_request.fetch()
        
        # fetch request from deserialized credentials
        if event.provider.provider_name == 'facebook':
            url = 'https://graph.facebook.com/me'
            rpc = Request(self.adapter, url, deserialized).fetch()
            
            resp = rpc.get_response()
            self.response.write('Bio:<br /><br />')
            self.response.write(resp.data)
            self.response.write('<br /><br />')
        
        user = user_rpc.get_response().user
        
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