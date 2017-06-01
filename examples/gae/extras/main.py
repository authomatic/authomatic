# main.py

import webapp2
from authomatic import Authomatic
from authomatic.adapters import Webapp2Adapter
from authomatic.extras import gae


authomatic = Authomatic(config=gae.ndb_config(),  # Here goes the config.
                        secret='some random secret string',
                        report_errors=False)

# Create a simple request handler for the login procedure.


class Login(webapp2.RequestHandler):

    # The handler must accept GET and POST http methods and
    # Accept any HTTP method and catch the "provider_name" URL variable.
    def any(self, provider_name):

        session = gae.Webapp2Session(self, secret='abc')

        # It all begins with login.
        result = authomatic.login(Webapp2Adapter(self),  # Framework adapter.
                                  provider_name,
                                  # Provider name extracted from url.
                                  session=session,
                                  session_saver=session.save)

        # Do not write anything to the response if there is no result!
        if result:
            # If there is result, the login procedure is over and we can write
            # to response.
            self.response.write('<a href="..">Home</a>')

            if result.error:
                # Login procedure finished with an error.
                self.response.write(
                    '<h2>Damn that error: {}</h2>'.format(result.error.message))

            elif result.user:
                # Hooray, we have the user!

                # OAuth 2.0 and OAuth 1.0a provide only limited user data on login,
                # We need to update the user to get more info.
                result.user.update()

                # Welcome the user.
                self.response.write('<h1>Hi {}</h1>'.format(result.user.name))
                self.response.write(
                    '<h2>Your id is: {}</h2>'.format(result.user.id))
                self.response.write(
                    '<h2>Your email is: {}</h2>'.format(result.user.email))

                # Seems like we're done, but there's more we can do...

                # If there are credentials (only by AuthorizationProvider),
                # we can _access user's protected resources.
                if result.user.credentials:

                    # Each provider has it's specific API.
                    if result.provider.name == 'fb':

                        self.response.write(
                            'Your are logged in with Facebook,<br />')

                        # We will access the user's 5 most recent statuses.
                        url = 'https://graph.facebook.com/{}?fields=feed.limit(5).fields(message)'
                        url = url.format(result.user.id)

                        # Access user's protected resource.
                        response = result.provider.access(url)

                        if response.status == 200:
                            # Parse response.
                            statuses = response.data.get('feed').get('data')
                            error = response.data.get('error')

                            if error:
                                self.response.write(
                                    'Damn that error: {}!'.format(error))
                            elif statuses:
                                self.response.write(
                                    'and these are your 5 most recent statuses:<br /><br />')
                                for message in statuses:

                                    text = message.get('message')
                                    date = message.get('created_time')

                                    self.response.write(
                                        '<h3>{}</h3>'.format(text))
                                    self.response.write(
                                        'Posted on: {}<br /><br />'.format(date))
                        else:
                            self.response.write(
                                'Damn that unknown error!<br />')
                            self.response.write(
                                'Status: {}'.format(response.status))

                    if result.provider.name == 'tw':

                        self.response.write(
                            'Your are logged in with Twitter,<br />')

                        # We will get the user's 5 most recent tweets.
                        url = 'https://api.twitter.com/1.1/statuses/user_timeline.json'

                        # You can pass a dictionary of querystring parameters.
                        response = result.provider.access(url, {'count': 5})

                        # Parse response.
                        if response.status == 200:
                            if isinstance(response.data, list):
                                # Twitter returns the tweets as a JSON list.
                                self.response.write(
                                    'and these are your 5 most recent tweets:')
                                for tweet in response.data:
                                    text = tweet.get('text')
                                    date = tweet.get('created_at')

                                    self.response.write(
                                        '<h3>{}</h3>'.format(text))
                                    self.response.write(
                                        'Tweeted on: {}'.format(date))

                            elif response.data.get('errors'):
                                self.response.write(
                                    'Damn that error: {}!'.format(
                                        response.data.get('errors')))
                        else:
                            self.response.write(
                                'Damn that unknown error!<br />')
                            self.response.write(
                                'Status: {}'.format(response.status))


# Create a home request handler just that you don't have to enter the urls
# manually.
class Home(webapp2.RequestHandler):

    def get(self):

        # Create links to the Login handler.
        self.response.write(
            'Login with <a href="login/fb">Facebook</a>.<br />')
        self.response.write('Login with <a href="login/tw">Twitter</a>.<br />')

        # Create OpenID form where the user can specify his claimed identifier.
        # The library by default extracts the identifier from the "id"
        # parameter.
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
app = webapp2.WSGIApplication(ROUTES, debug=True)
