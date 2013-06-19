from django.http import HttpResponse
from authomatic import Authomatic
from authomatic.adapters import DjangoAdapter

from config import CONFIG

authomatic = Authomatic(CONFIG, 'abcdef', report_errors=None)

def index(request):
    # Create links and OpenID form to the Login handler.
    return HttpResponse('''
        Login with <a href="login/fb">Facebook</a>.<br />
        Login with <a href="login/tw">Twitter</a>.<br />
        <form action="login/oi">
            <input type="text" name="id" value="me.yahoo.com" />
            <input type="submit" value="Authenticate With OpenID">
        </form>
    ''')

def login(request, provider_name):
    # We we need the response object for the adapter.
    response = HttpResponse()
    
    # Start the login procedure.
    result = authomatic.login(DjangoAdapter(request, response), provider_name)
     
    # If there is no result, the login procedure is still pendin.
    # Don't write anything to the response if there is no result!
    if result:
        # If there is result, the login procedure is over and we can write to response.
        response.write('<a href="..">Home</a>')
        
        if result.error:
            # Login procedure finished with an error.
            response.write('<h2>Damn that error: {}</h2>'.format(result.error.message))
        
        elif result.user:
            # Hooray, we have the user!
            
            # OAuth 2.0 and OAuth 1.0a provide only limited user data on login,
            # We need to update the user to get more info.
            if not (result.user.name and result.user.id):
                result.user.update()
            
            # Welcome the user.
            response.write('<h1>Hi {}</h1>'.format(result.user.name))
            response.write('<h2>Your id is: {}</h2>'.format(result.user.id))
            response.write('<h2>Your email is: {}</h2>'.format(result.user.email))
            
            # Seems like we're done, but there's more we can do...
            
            # If there are credentials (only by AuthorizationProvider),
            # we can _access user's protected resources.
            if result.user.credentials:
                
                # Each provider has it's specific API.
                if result.provider.name == 'fb':
                    response.write('Your are logged in with Facebook.<br />')
                    
                    # We will access the user's 5 most recent statuses.
                    url = 'https://graph.facebook.com/{}?fields=feed.limit(5)'
                    url = url.format(result.user.id)
                    
                    # Access user's protected resource.
                    access_response = result.provider.access(url)
                    
                    if access_response.status == 200:
                        # Parse response.
                        statuses = access_response.data.get('feed').get('data')
                        error = access_response.data.get('error')
                        
                        if error:
                            response.write('Damn that error: {}!'.format(error))
                        elif statuses:
                            response.write('Your 5 most recent statuses:<br />')
                            for message in statuses:
                                
                                text = message.get('message')
                                date = message.get('created_time')
                                
                                response.write('<h3>{}</h3>'.format(text))
                                response.write('Posted on: {}'.format(date))
                    else:
                        response.write('Damn that unknown error!<br />')
                        response.write('Status: {}'.format(response.status))
                    
                if result.provider.name == 'tw':
                    response.write('Your are logged in with Twitter.<br />')
                    
                    # We will get the user's 5 most recent tweets.
                    url = 'https://api.twitter.com/1.1/statuses/user_timeline.json'
                    
                    # You can pass a dictionary of querystring parameters.
                    access_response = result.provider.access(url, {'count': 5})
                                            
                    # Parse response.
                    if access_response.status == 200:
                        if type(access_response.data) is list:
                            # Twitter returns the tweets as a JSON list.
                            response.write('Your 5 most recent tweets:')
                            for tweet in access_response.data:
                                text = tweet.get('text')
                                date = tweet.get('created_at')
                                
                                response.write('<h3>{}</h3>'.format(text))
                                response.write('Tweeted on: {}'.format(date))
                                
                        elif response.data.get('errors'):
                            response.write('Damn that error: {}!'.\
                                                format(response.data.get('errors')))
                    else:
                        response.write('Damn that unknown error!<br />')
                        response.write('Status: {}'.format(response.status))
    
    return response

