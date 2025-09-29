# -*- coding: utf-8 -*-
# encoding: utf-8
import logging
import tornado.ioloop
import tornado.web

import authomatic
from authomatic.adapters import TornadoAdapter
from tests.functional_tests import fixtures


class HomeHandler(tornado.web.RequestHandler):
    """Home page handler for Tornado functional test"""

    def get(self):
        """Render home page"""
        self.write(fixtures.render_home('tornado'))


class LoginHandler(tornado.web.RequestHandler):
    """Login handler for OAuth authentication using TornadoAdapter"""

    def get(self, provider_name):
        """Handle GET requests for OAuth login"""
        self._handle_login(provider_name)

    def post(self, provider_name):
        """Handle POST requests for OAuth login"""
        self._handle_login(provider_name)

    def _handle_login(self, provider_name):
        """Handle OAuth login process"""
        # Create the authomatic instance
        authomatic_instance = authomatic.Authomatic(
            fixtures.ASSEMBLED_CONFIG,
            '123',
            report_errors=False
        )

        # Create the TornadoAdapter
        adapter = TornadoAdapter(self)

        # Perform the login
        result = authomatic_instance.login(adapter, provider_name)

        if result:
            # Login completed, render the result
            self.write(fixtures.render_login_result('tornado', result).encode())


def make_app(debug=True):
    """Create the Tornado application"""
    return tornado.web.Application([
        (r"/", HomeHandler),
        (r"/login/([^/]+)", LoginHandler),
    ], debug=debug)


if __name__ == '__main__':
    # Set up logging
    import logging
    logging.basicConfig(level=logging.INFO)

    # Create the application
    app = make_app(debug=True)

    # This does nothing unless you run this module with --testliveserver flag
    import liveandletdie
    liveandletdie.WsgirefSimpleServer.wrap(app)

    # Start the server
    port = 8080
    app.listen(port)
    print(f"Tornado functional test server starting on http://localhost:{port}")
    print(f"Visit http://localhost:{port}/ to run functional tests")

    try:
        tornado.ioloop.IOLoop.current().start()
    except KeyboardInterrupt:
        print("\nShutting down...")