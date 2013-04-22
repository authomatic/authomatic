# main.py

import urllib
import webapp2
import authomatic
from authomatic.adapters import Webapp2Adapter

from config import CONFIG


class Login(webapp2.RequestHandler):
    def any(self, provider_name):
        
        # Log the user in.
        result = authomatic.login(Webapp2Adapter(self), provider_name)
        
        if result:
            if result.user:
                result.user.update()
                self.response.write('<h1>Hi {}</h1>'.format(result.user.name))
                
                # Save the user name and ID to cookies that we can use it in other handlers.
                self.response.set_cookie('user_id', result.user.id)
                self.response.set_cookie('user_name', urllib.quote(result.user.name))
                
                if result.user.credentials:
                    # Serialize credentials and store it as well.
                    serialized_credentials = result.user.credentials.serialize()
                    self.response.set_cookie('credentials', serialized_credentials)
                    
            elif result.error:
                self.response.set_cookie('error', urllib.quote(result.error.message))
            
            self.redirect('/')


class Home(webapp2.RequestHandler):
    def get(self):
        # Create links to the Login handler.
        self.response.write('Login with <a href="login/fb">Facebook</a> or ')
        self.response.write('<a href="login/tw">Twitter</a>')
        
        # Retrieve values from cookies.
        serialized_credentials = self.request.cookies.get('credentials')
        user_id = self.request.cookies.get('user_id')
        user_name = urllib.unquote(self.request.cookies.get('user_name', ''))
        error = urllib.unquote(self.request.cookies.get('error', ''))
        
        if error:
            self.response.write('<p>Damn that error: {}</p>'.format(error))
        elif user_id:
            self.response.write('<h1>Hi {}</h1>'.format(user_name))
            
            if serialized_credentials:
                # Deserialize credentials.
                credentials = authomatic.credentials(serialized_credentials)
                
                name = credentials.provider_name
                
                self.response.write("""
                <p>You are logged in with <b>{}</b> and we have your credentials.</p>
                """.format(dict(fb='Facebook', tw='Twitter')[name]))
                
                valid = 'still' if credentials.valid else 'not anymore'
                expire_soon = 'less' if credentials.expire_soon(60 * 60 * 24) else 'more'
                remaining = credentials.expire_in
                expire_on = credentials.expiration_date
                
                self.response.write("""
                <p>
                    They are <b>{}</b> valid and
                    will expire in <b>{}</b> than one day
                    (in <b>{}</b> seconds to be precise).
                    It will be on <b>{}</b>.
                </p>
                """.format(valid, expire_soon, remaining, expire_on))
                
                if credentials.valid:
                    self.response.write("""
                    <p>We can refresh them while they are valid.</p>
                    <a href="refresh">OK, refresh them!</a>
                    <p>Moreover, we can do powerfull stuff with them.</p>
                    <a href="action/{}">Show me what you can do!</a>
                    """.format(credentials.provider_name))
                else:
                    self.response.write("""
                    <p>You must repeat the <b>login procedure</b>to get new credentials.</p>
                    <a href="login/{}">Refresh</a>
                    """.format(credentials.provider_name))
            
            self.response.write('<p>We can also log you out.</p>')
            self.response.write('<a href="logout">OK, log me out!</a>')


class Refresh(webapp2.RequestHandler):
    def get(self):
        self.response.write('<a href="..">Home</a>')
        
        serialized_credentials = self.request.cookies.get('credentials')
        credentials = authomatic.credentials(serialized_credentials)
        
        old_expiration = credentials.expiration_date
        
        response = credentials.refresh(force=True)
        
        if response:
            new_expiration = credentials.expiration_date
            
            if response.status == 200:
                self.response.write("""
                <p>
                    Credentials were refresshed successfully.
                    Their expiration date was extended from
                    <b>{}</b> to <b>{}</b>.
                </p>
                """.format(old_expiration, new_expiration))
            else:
                self.response.write("""
                <p>Refreshment failed!</p>
                <p>Status code: {}</p>
                <p>Error message:</p>
                <pre>{}</pre>
                """.format(response.status, response.content))
        else:
            self.response.write('<p>Your credentials don\'t support refreshment!</p>')
        
        self.response.write('<a href="">Try again!</a>')


class Action(webapp2.RequestHandler):
    def get(self, provider_name):
        if provider_name == 'fb':
            text = 'post a status on your Facebook timeline'
        elif provider_name == 'tw':
            text = 'tweet'
        
        self.response.write("""
        <a href="..">Home</a>
        <p>We can {} on your behalf.</p>
        <form method="post">
            <input type="text" name="message" value="Have you got a bandage?" />
            <input type="submit" value="Do it!">
        </form>
        """.format(text))
    
    def post(self, provider_name):
        self.response.write('<a href="..">Home</a>')
        
        # Retrieve the message from POST parameters and the values from cookies.
        message = self.request.POST.get('message')        
        serialized_credentials = self.request.cookies.get('credentials')
        user_id = self.request.cookies.get('user_id')
        
        if provider_name == 'fb':
            # Prepare the URL for Facebook Graph API.
            url = 'https://graph.facebook.com/{}/feed'.format(user_id)
            
            # Access user's protected resource.
            response = authomatic.access(serialized_credentials, url,
                                         params=dict(message=message),
                                         method='POST')
            
            # Parse response.
            post_id = response.data.get('id')
            error = response.data.get('error')
            
            if error:
                self.response.write('<p>Damn that error: {}!</p>'.format(error))
            elif post_id:
                self.response.write('<p>You just posted a status with id ' + \
                                    '{} to your Facebook timeline.<p/>'.format(post_id))
            else:
                self.response.write('<p>Damn that unknown error! Status code: {}</p>'\
                                    .format(response.status))
        
        elif provider_name == 'tw':
            
            response = authomatic.access(serialized_credentials,
                                         url='https://api.twitter.com/1.1/statuses/update.json',
                                         params=dict(status=message),
                                         method='POST')
            
            error = response.data.get('errors')
            tweet_id = response.data.get('id')
            
            if error:
                self.response.write('<p>Damn that error: {}!</p>'.format(error))
            elif tweet_id:
                self.response.write('<p>You just tweeted a tweet with id {}.</p>'.format(tweet_id))
            else:
                self.response.write('<p>Damn that unknown error! Status code: {}</p>'\
                                    .format(response.status))
        
        # Let the user repeat the action.
        self.response.write("""
        <form method="post">
            <input type="text" name="message" />
            <input type="submit" value="Do it again!">
        </form>
        """)


class Logout(webapp2.RequestHandler):
    def get(self):
        # Delete cookies.
        self.response.delete_cookie('user_id')
        self.response.delete_cookie('user_name')
        self.response.delete_cookie('credentials')
        
        # Redirect home.
        self.redirect('./')


# Create the routes.
ROUTES = [webapp2.Route(r'/login/<:.*>', Login, handler_method='any'),
          webapp2.Route(r'/refresh', Refresh),
          webapp2.Route(r'/action/<:.*>', Action),
          webapp2.Route(r'/logout', Logout),
          webapp2.Route(r'/', Home)]

authomatic.setup(config=CONFIG, secret='a-long-secret-string')

app = webapp2.WSGIApplication(ROUTES, debug=True)