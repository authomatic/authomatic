# main.py

from authomatic.adapters.gae.openid import NDBOpenIDStore
from config import CONFIG
import authomatic
import logging
import urllib
import webapp2


class Login(webapp2.RequestHandler):
    
    def anymethod(self, provider_name):
        
        result = authomatic.login(provider_name)
        
        if result:
            
            self.response.write('<a href="..">Home</a><br />')
            
            if result.error:
                
                self.response.write('Damn that error: {}!'.format(result.error.message))
            
            elif result.user:
                
                logging.info('OK')
                
                result.user.update()
                
                self.response.write('Hi {},<br />'.format(result.user.name))
                
                if result.user.credentials:
                    
                    # You can serialize the credentials to a minimized string...
                    serialized_credentials = result.user.credentials.serialize()
                    
                    # ...and store it somewhere for later.
                    # You will probably store it to some user datamodel,
                    # I used cookies only for the sake of simplicity.
                    self.response.set_cookie('credentials', serialized_credentials)
                    
                    # We will also need user ID.
                    self.response.set_cookie('user_id', result.user.id)
                    
                    
                    button_label = 'Submit'
                    
                    # Write a message depending on provider.
                    if result.provider.name == 'fb':
                        self.response.write('Write something to your Facebook timeline!')
                        button_label = 'Post to Facebook!'
                    elif result.provider.name == 'tw':
                        self.response.write('Tweet something!')
                        button_label = 'Tweet!'
                    elif result.provider.name == 'google':
                        self.response.write('Google+ something!')
                        button_label = 'Post to Google+!'
                    
                    # Create a simple form and submit it to the Action handler.
                    self.response.write("""
                    <form action="../action" method="post">
                        <input type="text" name="message" value="Can it be that it is all so simple now?" />
                        <input type="submit" value="{}">
                    </form>
                    """.format(button_label))


class Action(webapp2.RequestHandler):
    """
    This handler will process the form submit.
    """
    
    # Accept HTTP POST only
    def post(self):
        
        self.response.write('<a href="..">Home</a><br />')
        
        # Retrieve the values from cookies
        message = self.request.POST.get('message')        
        serialized_credentials = self.request.cookies.get('credentials')
        user_id = self.request.cookies.get('user_id')
        
        # Now it's time to deserialize credentials.
        credentials = authomatic.credentials(serialized_credentials)
                
        # The OAuth 2.0 credentials (the access token) have limited lifetime.
        
        # We can check the expiration date of the credentials,
        expiration_time = credentials.expiration_time
        self.response.write('Credentials expire on {}.<br />'.format(expiration_time))
        
        # whether it has not expired allready,
        valid = credentials.valid
        self.response.write('Credentials are valid: {}.<br />'.format(valid))
        
        # or whether it will expire soon.
        # The function has the same signature as datetime.timedelta().
        expires_soon = credentials.expires_soon(60 * 60 * 24)
        self.response.write('Credentials expire in less than one day: {}.<br />'.format(expires_soon))
        
        # You can refresh the credentials at any time but it must not be expired!
        # We need to pass adapter and CONFIG to the method because internaly it
        # fetches the provider's access token url.
        # The method updates the credentials instance and returns a Response instance.
        response = credentials.refresh()
        
        # The refreshment of credentials is OAuth 2.0 specific feature and
        # the method returns None if it is called by other provider types.
        if response:
            if response.status == 200:
                self.response.write('Credentials were refreshed successfully!<br />')
                expiration_time = credentials.expiration_time
                self.response.write('Credentials expire on {}.<br />'.format(expiration_time))
            else:
                self.response.write('Credentials refreshment failed!<br />')
                self.response.write('status code: {}<br />'.format(response.status))
                self.response.write('content: {}<br />'.format(response.content))
        else:
            self.response.write('Credentials do not support refreshment!<br />')
        
        
        if credentials.provider_name == 'google':
            pass        
        
        # Credentials know the provider name.
        if credentials.provider_name == 'fb':
            
            self.response.write('Credentials expire on {}.<br />'.format(credentials.expiration_time))
            self.response.write('Credentials token {}.<br />'.format(credentials.token))
            self.response.write('Credentials refresh_token {}.<br />'.format(credentials.refresh_token))
            self.response.write('<br />-------------------REFRESH-----------------<br />')
            
            response = credentials.refresh()
            
            if response:
                self.response.write('status = {}<br />'.format(response.status))
                self.response.write('content = {}<br /><br />'.format(response.content))
            
            self.response.write('Credentials expire on {}.<br />'.format(credentials.expiration_time))
            self.response.write('Credentials token {}.<br />'.format(credentials.token))
            self.response.write('Credentials refresh_token {}.<br /><br /><br />'.format(credentials.refresh_token))
            
            
            
            # OAuth 2.0 credentials (the access token) have limited lifetime.
            
            # We can check the expiration date of the credentials,
            expiration_time = credentials.expiration_time
            self.response.write('Credentials expire on {}.<br />'.format(expiration_time))
            
            # whether it has not expired allready,
            valid = credentials.valid
            self.response.write('Credentials are valid: {}.<br />'.format(valid))
            
            # or whether it will expire soon.
            expires_soon = credentials.expires_soon(60 * 60 * 24)
            self.response.write('Credentials expire in less than one day: {}.<br /><br />'.format(expires_soon))
            
            # An expiring access token can be exchanged for a fresh one by the provider.
            # This is provider specific so I leave it up to you to find out how.
                        
            # Prepare the URL for Facebook Graph API
            url = 'https://graph.facebook.com/{}/feed?message={}'.format(user_id, message)
            
            # Access user's protected resource.
            response = authomatic.access(credentials, url, 'POST')
            
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
        
        if credentials.provider_name == 'tw':
            
            # Prepare the Twitter API URL.
            url = 'https://api.twitter.com/1.1/statuses/update.json?status={}'.format(message)
            
             # Access user's protected resource.
            response = authomatic.access(credentials, url, 'POST')
            
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
        
        # Make another form that the user can repeat the action.
        self.response.write("""
        <form method="post">
            <input type="text" name="message" />
            <input type="submit" value="Do it again!">
        </form>
        """)


# Create a home request handler just that you don't have to enter the urls manually.
class Home(webapp2.RequestHandler):
    
    def get(self):
        
        # Create links to the Login handler.
        self.response.write('Login with <a href="auth/fb">Facebook</a>.<br />')
        self.response.write('Login with <a href="auth/google">Google</a>.<br />')
        self.response.write('Login with <a href="auth/tw">Twitter</a>.<br />')


# Finally create the routes.
ROUTES = [webapp2.Route(r'/auth/<:.*>', Login, handler_method='anymethod'),
          webapp2.Route(r'/action', Action),
          webapp2.Route(r'/', Home)]

# Wrap the WSGI app in middleware.
app = authomatic.middleware(webapp2.WSGIApplication(ROUTES, debug=True),
                            config=CONFIG,
                            report_errors=True)




