import webapp2

class Test(webapp2.RequestHandler):
    def any(self):
        self.response.write('TEST:\n<br />\n')
        self.response.write('headers = {}\n<br />\n'.format(self.request.headers))
        self.response.write('params = {}\n<br />\n'.format(self.request.params))
        self.response.write('body = {}\n<br />\n'.format(self.request.body))


ROUTES = [webapp2.Route(r'/test', Test, handler_method='any'),]

app = webapp2.WSGIApplication(ROUTES, debug=True)