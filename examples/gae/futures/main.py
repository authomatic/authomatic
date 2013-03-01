# main.py

from config import CONFIG
import authomatic
import logging
import time
import webapp2
import timeit

# Create a simple request handler for the login procedure.
class Login(webapp2.RequestHandler):
    
    def any(self, provider_name):
        self.response.write('<a href="..">Home</a>')
        self.response.write('<br /><a href="fb">FB</a>')
        self.response.write('<br /><a href="tw">TW</a>')
                
        # Log the user in.
        result = authomatic.login(provider_name)
        
        if result.error:
            self.response.write('<h2>Damn that error: {}</h2>'.format(result.error.message))
        elif result.user:
            result.user.update()
            
            
            
            # Welcome the user.
            self.response.write('<h1>Hi {}</h1>'.format(result.user.name))
            self.response.write('<h2>Your id is: {}</h2>'.format(result.user.id))
            self.response.write('<h2>Your email is: {}</h2>'.format(result.user.email))
            
            if result.user.credentials:
                if result.provider.name == 'fb':
                    self.response.write('Your are logged in with Facebook,<br />')
                    
                    
                    # We will access the user's 5 most recent likes.
                    url = 'https://graph.facebook.com/{}'.format(result.user.id)
                    
#                    future = result.provider.async_access(url, params=dict(fields='likes.limit(5)'))
                    
#                    future = authomatic.async_access(result.user.credentials, url,
#                                               params=dict(fields='likes.limit(5)'))
                    
#                    future = result.user.credentials.async_refresh(force=True)
                    
                    start = time.time()
                    self.response.write('<h4>Start: {}</h4>'.format(start))
                    
                    now = time.time()
                    duration = now - start
                    start = now
                    self.response.write('<h4>Sleeping {}</h4>'.format(duration))
                    
                    time.sleep(2)
                    
                    now = time.time()
                    duration = now - start
                    start = now
                    self.response.write('<h4>Woke up {}</h4>'.format(duration))
                    
                    response = future.get_result()
                    
                    now = time.time()
                    duration = now - start
                    start = now
                    self.response.write('<h4>Got result {}</h4>'.format(duration))
                    
                    self.response.write('<pre>{}</pre>'.format(response.content))               


# Create a home request handler just that you don't have to enter the urls manually.
class Home(webapp2.RequestHandler):
    
    def get(self):
        
        # Create links to the Login handler.
        self.response.write('Login with <a href="login/fb">Facebook</a>.<br />')
        self.response.write('Login with <a href="login/tw">Twitter</a>.<br />')
        
        # Create OpenID form where the user can specify his claimed identifier.
        # The library by default extracts the identifier from the "id" parameter.
        self.response.write('''
            <form action="login/oi">
                <input type="text" name="id" value="me.yahoo.com" />
                <input type="submit" value="Authenticate With OpenID">
            </form>
        ''')
        
        # Create GAEOpenID form
        self.response.write('''
            <form action="login/gae_oi">
                <input type="text" name="id" value="me.yahoo.com" />
                <input type="submit" value="Authenticate With GAEOpenID">
            </form>
        ''')


# Create routes.
ROUTES = [webapp2.Route(r'/login/<:.*>', Login, handler_method='any'),
          webapp2.Route(r'/', Home)]

# Instantiate the webapp2 WSGI application.
webapp_app = webapp2.WSGIApplication(ROUTES, debug=True)

# Finally wrapp the app in authomatic middleware.
app = authomatic.middleware(webapp_app,
                            config=CONFIG, # Here goes the config.
                            secret='some random secret string')