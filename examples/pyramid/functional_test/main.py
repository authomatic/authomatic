# main.py

import liveandletdie
from pyramid.config import Configurator
from pyramid.response import Response
from wsgiref.simple_server import make_server

from authomatic import Authomatic
from authomatic.adapters import WebObAdapter
from tests.functional_tests import fixtures


authomatic = Authomatic(fixtures.ASSEMBLED_CONFIG, '123', report_errors=False)


def home(request):
    return Response(fixtures.render_home('pyramid'))


def login(request):
    provider_name = request.matchdict.get('provider_name')
    response = Response()
    result = authomatic.login(WebObAdapter(request, response), provider_name)

    if result:
        response.write(
            fixtures.render_login_result(
                'pyramid', result).encode())

    return response


if __name__ == '__main__':
    config = Configurator()

    config.add_route('home', '/')
    config.add_view(home, route_name='home')

    config.add_route('login', '/login/{provider_name}')
    config.add_view(login, route_name='login')

    app = config.make_wsgi_app()
    liveandletdie.WsgirefSimpleServer.wrap(app)

    server = make_server('127.0.0.1', 8080, app)
    server.serve_forever()
