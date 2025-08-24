# -*- coding: utf-8 -*-

from wsgiref.simple_server import make_server
from pyramid.config import Configurator
from pyramid.response import Response
from authomatic import Authomatic
from authomatic.adapters import WebObAdapter
from authomatic.providers import oauth2

CLIENT_ID = 'client-id-from-dashboard.dataporten.no'
CLIENT_SECRET = 'client-secret-from-dashboard.dataporten.no'

CONFIG = {
    'dp': {
        'class_': oauth2.Dataporten,
        'consumer_key': CLIENT_ID,
        'consumer_secret': CLIENT_SECRET
    }
}

SECRET = 'ergeresf'  # Used for signing session cookies and salting CSRF tokens
AUTHOMATIC = Authomatic(config=CONFIG, secret=SECRET)


def login(request):
    response = Response()
    result = AUTHOMATIC.login(WebObAdapter(request, response), 'dp')
    if result:
        # If there is a result, the login procedure is over and we can write to response.
        response.write('<a href="..">Home</a>')
        if result.error:
            response.write(u'<h2>Login failed: {0}</h2>'.format(result.error.message))
        elif result.user:
            # OAuth 2.0 provides only limited user data on login,
            # We need to update the user to get more info.
            if not (result.user.name and result.user.id):
                result.user.update()
            response.write(u'<h1>Hi {0}</h1>'.format(result.user.name))
            response.write(u'<h2>Your id is: {0}</h2>'.format(result.user.id))
            response.write(u'<h2>Your email is: {0}</h2>'.format(result.user.email))
    return response


def home(request):
    return Response('''
        Login with <a href="login">Dataporten</a>.<br />
    ''')


if __name__ == '__main__':
    config = Configurator()
    config.add_route('home', '/')
    config.add_view(home, route_name='home')
    config.add_route('login', '/login')
    config.add_view(login, route_name='login')
    app = config.make_wsgi_app()
    server = make_server('127.0.0.1', 8080, app)
    server.serve_forever()
