# main.py

import webapp2
from authomatic.adapters import gae
import authomatic
from config import CONFIG


# Create a simple request handler for the login procedure.
class Login(webapp2.RequestHandler):
    
    # The handler must accept GET and POST http methods.
    # Accept the "provider_name" URL variable.
    def anymethod(self, provider_name):
                
        # Create an adapter for Webapp2 framework.
        adapter = gae.Webapp2Adapter(self, session_secret='abcdef')
        
        # We now have everything to get the user from provider.
        result = authomatic.login(adapter, CONFIG, provider_name)
        
        # Dont write anything to the response if there is no result!!!
        
        if result:
            
            # If there is result, the login procedure has finished,
            # And you can write to the response.
            self.response.write('<a href="..">Home</a><br />!')
            
            if result.error:
                # Login procedure finished with an error.
                self.response.write('Damn that error: {}!'.format(result.error.message))
            
            elif result.user:
                # Hooray, we have the user!
                
                # But wait, we need to update his info first.
                # This is only neccessary by AuthorisationProvider i.e. OAuth 2.0 and OAuth 1.0a.
                result.user.update()
                
                # Welcome the user.
                self.response.write('Hi {},<br />'.format(result.user.name))
                self.response.write('Your id is: {}<br />'.format(result.user.id))
                self.response.write('Your email is: {}<br />'.format(result.user.email))
                
                # Seems like we're done, but there's more we can do...
                
                # If there are credentials (only by AuthorisationProvider),
                # we can access user's protected resources.
                if result.user.credentials:
                    
                    # Each provider has it's specific API.
                    if result.provider.name == 'fb':
                        
                        self.response.write('Your are logged in with Facebook.<br />')
                        
                        # We will post this message to the user's Facebook timeline.
                        message = 'Can it be that it is all so simple now?'
                        
                        # Construct the Facebook Graph API URL.
                        url = 'https://graph.facebook.com/{}/feed?message={}'.format(result.user.id, message)
                        
                        # Post to timeline on user's behalf (access his protected resource).
                        response = result.provider.fetch(url, method='POST')
                        
                        # Parse response.
                        post_id = response.data.get('id')
                        error = response.data.get('error')
                        
                        # We're done!
                        if error:
                            self.response.write('Damn that error: {}!'.format(error))
                        elif post_id:
                            self.response.write('You just posted a post with id ' + \
                                                '{} to your Facebook timeline!'.format(post_id))
                        else:
                            self.response.write('Damn that unknown error!')
                        
                    if result.provider.name == 'tw':
                        
                        self.response.write('Your are logged in with Twitter.<br />')
                        
                        # We will tweet this message on the users timeline.
                        status = 'Can it be that it is all so simple now?'
                        
                        # Construct the Twitter API URL
                        # Note: You need to set your Twitter app access to "Read and Write"!
                        url = 'https://api.twitter.com/1.1/statuses/update.json?status={}'.format(status)
                        
                        # Tweet on user's behalf (access his protected resource).
                        response = result.provider.fetch(url, method='POST')
                        
                        # Parse response.
                        error = response.data.get('errors')
                        tweet_id = response.data.get('id')
                        
                        # We're done!
                        if error:
                            self.response.write('Damn that error: {}!'.format(error))
                        elif tweet_id:
                            self.response.write('You just tweeted a tweet with id {}!'.format(tweet_id))
                        else:
                            self.response.write('Damn that unknown error!')


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


# Finally create the routes.
ROUTES = [webapp2.Route(r'/login/<:.*>', Login, handler_method='anymethod'),
          webapp2.Route(r'/', Home)]

# And instantiate the WSGI application.
app = webapp2.WSGIApplication(ROUTES, debug=True)




