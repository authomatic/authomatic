import webapp2
import routes



app = webapp2.WSGIApplication(routes.ROUTES, debug=True)