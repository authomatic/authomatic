
import sys

import webapp2
from authomatic.adapters import Webapp2Adapter
from authomatic import Authomatic

import config


authomatic = Authomatic(secret='YAhe[#{^VlX-cK/$ki:$</vu!B5rTW9xi:fbN/%i pIx@AH}0c/ke4M%|c9*H4#>',
                        config=config.PROVIDERS,
                        report_errors=False,
                        debug=True)


def headers(handler):

    handler.response.write('<a href="/auth/facebook">Facebook</a><br />')
    handler.response.write('<a href="/auth/google">Google</a><br />')
    handler.response.write(
        '<a href="/auth/windows_live">Windows Live</a><br />')
    handler.response.write('<a href="/auth/twitter">Twitter</a><br />')

    handler.response.write('<br />')
    handler.response.write('Open ID:<br />')

    handler.response.write(
        '<a href="/auth/gaeoi?id=https://me.yahoo.com">GAEOpenID Yahoo</a><br />')

    handler.response.write('<br />')
    handler.response.write('AX:<br />')

    handler.response.write(
        '<a href="/auth/oi?id=https://me.yahoo.com">OpenID Yahoo</a><br />')
    handler.response.write(
        '<a href="/auth/oi?id=https://www.google.com/accounts/o8/id">OpenID Google</a><br />')

    handler.response.write('<br />')
    handler.response.write('SREG:<br />')

    handler.response.write(
        '<a href="/auth/oi?id=peterhudec.myid.net">peterhudec.myid.net</a><br />')
    handler.response.write(
        '<a href="/auth/oi?id=https://peterhudec.myvidoop.com">peterhudec.myvidoop.com</a> (PAPE) Returns nothing!<br />')
    handler.response.write(
        '<a href="/auth/oi?id=peterhudec.pip.verisignlabs.com">peterhudec.pip.verisignlabs.com</a><br />')
    handler.response.write(
        '<a href="/auth/oi?id=http://peterhudec.signon.com">peterhudec.signon.com</a> Returns nothing!<br />')
    handler.response.write(
        '<a href="/auth/oi?id=http://peterhudec.myopenid.com/">peterhudec.myopenid.com</a> (PAPE) POST is not alloved!<br />')

    handler.response.write('<br /><br />')


class Home(webapp2.RequestHandler):
    def any(self):
        headers(self)


class Login(webapp2.RequestHandler):

    def login(self, provider_name):

        result = authomatic.login(Webapp2Adapter(self),
                                  provider_name,
                                  callback=self.callback)

        if result:
            if result.user:
                user_response = result.user.update()
                if user_response:
                    self.response.write(
                        f'<br /><br />status = {user_response.status}<br />')

                self.response.write(
                    f'<br /><br />Hi {result.user.name}<br />')
                self.response.write(
                    f'your ID is {result.user.id}<br />')
                self.response.write(
                    f'your email is {result.user.email}<br />')
            elif result.error:
                self.response.write(
                    f'ERROR {result.error.message}<br />')

    def callback(self, event):

        headers(self)

        if event.error:
            self.response.write('ERROR:')
            self.response.write('<br /><br />')

            self.response.write(
                f'message: {event.error.message}<br />')
            for k, v in event.error.__dict__.iteritems():
                if not k == 'message':
                    self.response.write(f'{k}: {v}<br />')

        elif event.user:

            self.response.write('<br /><br />')
            self.response.write(f'user = {event.user}<br /><br />')

            if event.user.credentials:

                self.response.write('<br /><br />')
                self.response.write('Credentials:<br /><br />')

                for k, v in event.user.credentials.__dict__.items():
                    self.response.write(f'{k}: {v}<br />')

                serialized = event.user.credentials.serialize()

                deserialized = authomatic.credentials(serialized)

                self.response.write('<br /><br />')
                self.response.write(
                    f'Serialized:<br />{serialized}<br /><br />')
                self.response.write(
                    f'Serialized size:<br />{sys.getsizeof(serialized)} B<br /><br />')

                # deserialized credentials
                for k, v in deserialized.__dict__.items():
                    self.response.write(f'{k}: {v}<br />')

                self.response.write('<br /><br />')
                self.response.write('User Info:<br /><br />')
                self.response.write('<br /><br />')

                event.user.update()

            for k, v in event.user.__dict__.iteritems():
                if k != 'data':
                    self.response.write(f'{k}: {v}<br />')
                    if k == 'gae_user' and v:
                        for kk, vv in v.__dict__.iteritems():
                            self.response.write(
                                f'&nbsp;&nbsp;&nbsp;{kk}: {vv}<br />')

            self.response.write('<br /><br />')
            self.response.write('Raw User Info:<br /><br />')
            self.response.write(event.user.data)


class Test(webapp2.RequestHandler):
    def any(self):
        self.response.write('TEST:\n')
        self.response.write(f'headers = {self.request.headers}\n')
        self.response.write(f'params = {self.request.params}\n')
        self.response.write(f'body = {self.request.body}\n')


ROUTES = [webapp2.Route(r'/auth/<:.*>', Login, 'auth', handler_method='login'),
          webapp2.Route(r'/test', Test, handler_method='any'),
          webapp2.Route(r'/', Home, handler_method='any'), ]

app = webapp2.WSGIApplication(ROUTES, debug=True)
