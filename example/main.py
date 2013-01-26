from simpleauth2 import Credentials, Request
from simpleauth2.adapters.gaewebapp2 import GAEWebapp2Adapter
from simpleauth2.adapters.gaewebapp2.openid import NDBOpenIDStore
import config
import simpleauth2
import sys
import webapp2

def headers(handler):
    handler.response.write('<a href="/auth/facebook">Facebook</a><br />')
    handler.response.write('<a href="/auth/google">Google</a><br />')
    handler.response.write('<a href="/auth/windows_live">Windows Live</a><br />')
    handler.response.write('<a href="/auth/twitter">Twitter</a><br />')
    
    handler.response.write('<br />')
    handler.response.write('Open ID:<br />')
    
    handler.response.write('<br />')
    handler.response.write('AX:<br />')
    
    handler.response.write('<a href="/auth/oi?id=https://me.yahoo.com">OpenID Yahoo</a><br />')
    handler.response.write('<a href="/auth/oi?id=https://www.google.com/accounts/o8/id">OpenID Google</a><br />')
            
    handler.response.write('<br />')
    handler.response.write('SREG:<br />')
    
    handler.response.write('<a href="/auth/oi?id=peterhudec.myid.net">peterhudec.myid.net</a><br />')
    handler.response.write('<a href="/auth/oi?id=https://peterhudec.myvidoop.com">peterhudec.myvidoop.com</a> (PAPE) Returns nothing!<br />')
    handler.response.write('<a href="/auth/oi?id=peterhudec.pip.verisignlabs.com">peterhudec.pip.verisignlabs.com</a><br />')
    handler.response.write('<a href="/auth/oi?id=http://peterhudec.signon.com">peterhudec.signon.com</a> Returns nothing!<br />')
    handler.response.write('<a href="/auth/oi?id=http://peterhudec.myopenid.com/">peterhudec.myopenid.com</a> (PAPE) POST is not alloved!<br />')
    
    handler.response.write('<br /><br />')
    

class Home(webapp2.RequestHandler):
    def get(self):
        headers(self)        
        

class Login(webapp2.RequestHandler):
    
    def login(self, provider_name):
        
        
        self.adapter = GAEWebapp2Adapter(handler=self,
                                    providers_config=config.PROVIDERS,
                                    session_secret='abcd',
                                    openid_store=NDBOpenIDStore)
        
        self.adapter.login(provider_name, self.callback, oi_identifier=self.request.params.get('id'),
                           report_errors=True)
    
    def callback(self, event):
        
        headers(self)
        
        if event.error:
            self.response.write('ERROR:')
            self.response.write('<br /><br />')
            
            self.response.write('message: {}<br />'.format(event.error.message))
            for k, v in event.error.__dict__.iteritems():
                if not k == 'message':
                    self.response.write('{}: {}<br />'.format(k, v))
        
        else:
            if event.credentials:
                
                self.response.write('<br /><br />')
                self.response.write('Credentials:<br /><br />')
                
                for k, v in event.credentials.__dict__.items():
                    self.response.write('{}: {}<br />'.format(k, v))        
                
                serialized = event.credentials.serialize()
                
                deserialized = Credentials.deserialize(self.adapter, serialized)
                
                self.response.write('<br /><br />')
                self.response.write('Serialized:<br />{}<br /><br />'.format(serialized)) 
                self.response.write('Serialized size:<br />{} B<br /><br />'.format(sys.getsizeof(serialized)))        
                
                # deserialized credentials
                for k, v in deserialized.__dict__.items():
                    self.response.write('{}: {}<br />'.format(k, v))
            
            if event.provider.has_protected_resources:
                # fetch user info asynchronously
                event.provider.user_info_request.fetch()
                
                
                # fetch user info request the easy way
                user_rpc = event.provider.user_info_request.fetch()
                
                # fetch request from deserialized credentials
                if event.provider.provider_name == 'facebook':
                    url = 'https://graph.facebook.com/me'
                    rpc = Request(self.adapter, url, serialized).fetch()
                    
                    resp = rpc.get_response()
                    self.response.write('Bio:<br /><br />')
                    self.response.write(resp.data)
                
                user = user_rpc.get_response().user
            else:
                user = event.get_user()
            
            if user:
                self.response.write('<br /><br />')
                self.response.write('User Info:<br /><br />')
                self.response.write('<br /><br />')
                
                for k, v in user.__dict__.iteritems():
                    if k != 'raw_user_info':
                        self.response.write('{}: {}<br />'.format(k, v))
                        if k == 'gae_user' and v:
                            for kk, vv in v.__dict__.iteritems():
                                self.response.write('&nbsp;&nbsp;&nbsp;{}: {}<br />'.format(kk, vv))
                        
                
                self.response.write('<br /><br />')
                self.response.write('Raw User Info:<br /><br />')
                self.response.write(user.raw_user_info)




# routes must be named
ROUTES = [webapp2.Route(r'/auth/<:.*>', Login, 'auth', handler_method='login'),
          webapp2.Route(r'/', Home)]

app = webapp2.WSGIApplication(ROUTES, debug=True)