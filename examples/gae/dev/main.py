# -*- coding: utf-8 -*-

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
                        '<br /><br />status = {0}<br />'.format(user_response.status))

                self.response.write(
                    '<br /><br />Hi {0}<br />'.format(result.user.name))
                self.response.write(
                    'your ID is {0}<br />'.format(result.user.id))
                self.response.write(
                    'your email is {0}<br />'.format(result.user.email))
            elif result.error:
                self.response.write(
                    'ERROR {0}<br />'.format(result.error.message))

    def callback(self, event):

        headers(self)

        if event.error:
            self.response.write('ERROR:')
            self.response.write('<br /><br />')

            self.response.write(
                'message: {0}<br />'.format(event.error.message))
            for k, v in event.error.__dict__.iteritems():
                if not k == 'message':
                    self.response.write('{0}: {1}<br />'.format(k, v))

        elif event.user:

            self.response.write('<br /><br />')
            self.response.write('user = {0}<br /><br />'.format(event.user))

            if event.user.credentials:

                self.response.write('<br /><br />')
                self.response.write('Credentials:<br /><br />')

                for k, v in event.user.credentials.__dict__.items():
                    self.response.write('{0}: {1}<br />'.format(k, v))

                serialized = event.user.credentials.serialize()

                deserialized = authomatic.credentials(serialized)

                self.response.write('<br /><br />')
                self.response.write(
                    'Serialized:<br />{0}<br /><br />'.format(serialized))
                self.response.write(
                    'Serialized size:<br />{0} B<br /><br />'.format(sys.getsizeof(serialized)))

                # deserialized credentials
                for k, v in deserialized.__dict__.items():
                    self.response.write('{0}: {1}<br />'.format(k, v))

                self.response.write('<br /><br />')
                self.response.write('User Info:<br /><br />')
                self.response.write('<br /><br />')

                event.user.update()

            for k, v in event.user.__dict__.iteritems():
                if k != 'data':
                    self.response.write('{0}: {1}<br />'.format(k, v))
                    if k == 'gae_user' and v:
                        for kk, vv in v.__dict__.iteritems():
                            self.response.write(
                                '&nbsp;&nbsp;&nbsp;{0}: {1}<br />'.format(kk, vv))

            self.response.write('<br /><br />')
            self.response.write('Raw User Info:<br /><br />')
            self.response.write(event.user.data)


class Test(webapp2.RequestHandler):
    def any(self):
        self.response.write('TEST:\n')
        self.response.write('headers = {0}\n'.format(self.request.headers))
        self.response.write('params = {0}\n'.format(self.request.params))
        self.response.write('body = {0}\n'.format(self.request.body))


ROUTES = [webapp2.Route(r'/auth/<:.*>', Login, 'auth', handler_method='login'),
          webapp2.Route(r'/test', Test, handler_method='any'),
          webapp2.Route(r'/', Home, handler_method='any'), ]

app = webapp2.WSGIApplication(ROUTES, debug=True)
