import handlers
import webapp2

ROUTES = [('/', handlers.Home),
          webapp2.Route(r'/auth/<:.*>', handler=handlers.Login, name='login')]