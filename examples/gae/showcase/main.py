# -*- coding: utf-8 -*-

import os
import json
import logging

import jinja2
import webapp2
import authomatic
from authomatic.adapters import Webapp2Adapter

# import config
import config_public as config


authomatic.setup(config=config.config,
                 secret=config.SECRET,
                 report_errors=True,
                 logging_level=logging.DEBUG)


def render(handler, result=None, popup_js=''):
    handler.rr('home.html',
               result=result,
               popup_js=popup_js,
               title='Authomatic Example',
               base_url='http://authomatic-example.appspot.com',
               oauth1=sorted(config.OAUTH1.items()),
               oauth2=sorted(config.OAUTH2.items()))


class BaseHandler(webapp2.RequestHandler):
    """
    Base handler which adds jinja2 templating.
    """
    
    @webapp2.cached_property
    def jinja2_environment(self):
        path = os.path.join(os.path.dirname(__file__), 'templates')
        return jinja2.Environment(loader=jinja2.FileSystemLoader(path))
    
    def rr(self, template, **context):
        template = self.jinja2_environment.get_template(template)
        self.response.write(template.render(context))


class Home(BaseHandler):
    def get(self):
        render(self)


class Login(BaseHandler):
    def any(self, provider_name):
        result = authomatic.login(Webapp2Adapter(self), provider_name)
        if result:
            apis = []
            if result.user:
                result.user.update()
                if result.user.credentials:
                    apis = config.config.get(provider_name, {}).get('_apis', {})
            
            nice_provider_name = config.config.get(provider_name, {}).get('_name') or provider_name.capitalize()
            
            render(self, result, result.popup_js(custom=dict(apis=apis, provider_name=nice_provider_name)))


ROUTES = [webapp2.Route(r'/login/<:.*>', Login, handler_method='any'),
          webapp2.Route(r'/', Home, name='home')]


app = webapp2.WSGIApplication(ROUTES, debug=True)
