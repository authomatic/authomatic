import config
import simpleauth2
import webapp2
import logging

class Login(webapp2.RequestHandler):
    
    def get(self, provider_name):
        
        sa2 = simpleauth2.Simpleauth2(self, config.PROVIDERS, config.SESSION)
        sa2.login(provider_name, self.callback)
        #self.simpleauth2.login(provider_name, self.callback)
    
    def callback(self, event):
                
        # fetch user info asynchronously
        event.provider.user_info_request.fetch()
               
        self.response.write('Type: {}<br /><br />'.format(event.provider.type))
        self.response.write('Name: {}<br /><br />'.format(event.provider.provider_name))
        
        self.response.write(event.access_token)
        self.response.write('<br /><br />')
        self.response.write(event.expires)
        self.response.write('<br /><br />')
                
        self.response.write('<br /><br />')
        self.response.write('<a href="/auth/facebook">Facebook</a><br />')
        self.response.write('<a href="/auth/google">Google</a><br />')
        self.response.write('<a href="/auth/windows_live">Windows Live</a><br />')
        self.response.write('<a href="/auth/twitter">Twitter</a><br />')
        
        # if Facebook
        if type(event.provider) == simpleauth2.providers.Facebook:
            
            music_request = event.provider.create_request('https://graph.facebook.com/me/music').fetch()
            music_request.fetch()
            music = music_request.get_result().data
            
            self.response.write('Music:<br /><br />')
            self.response.write(music)
            self.response.write('<br /><br />')
        
        
        # if Twitter
        if type(event.provider) == simpleauth2.providers.Twitter:
            
            self.response.write('Its Twitter<br /><br />')
        
        # get result of asynchronous call
        user_info = event.provider.user_info_request.get_result()
        
        for k, v in user_info.__dict__.items():
            if k != 'raw_user_info':
                self.response.write('{}: {}<br />'.format(k, v))

# routes must be named
ROUTES = [webapp2.Route(r'/auth/<:.*>', Login, 'auth')]

app = webapp2.WSGIApplication(ROUTES, debug=True)