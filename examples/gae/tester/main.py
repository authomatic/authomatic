
import cgi
import logging

import webapp2
import authomatic
from authomatic.adapters import Webapp2Adapter

from config import CONFIG

def links(handler):
    for p in CONFIG.keys():
        handler.response.write('<a href="login/{p}">{p}</a><br />'.format(p=p))
    handler.response.write('<br /><br />')


def loop(handler, obj):
    handler.response.write('<table>')
    for k, v in obj.__dict__.items():
        if not k in ('data', 'gae_user', 'credentials', 'content'):
            style = 'color: red' if not v else ''
            handler.response.write('<tr style="{}"><td>{}:</td><td>{}</td></tr>'.format(style, k, v))
    handler.response.write('</table>')


class Login(webapp2.RequestHandler):
    def any(self, provider_name):
        
        result = authomatic.login(Webapp2Adapter(self), provider_name)
        
        if result:
            self.response.write("""<!DOCTYPE html><html>
            <head>
                <script src="https://google-code-prettify.googlecode.com/svn/loader/run_prettify.js?skin=sunburst"></script>
            </head>
            """)
            
            self.response.write('<body>')
            self.response.write('<a href="..">Home</a> | ')
            self.response.write('<a href="../login/{}">Retry</a>'.format(provider_name))
            
            if result.error:
                self.response.write('<h4>ERROR: {}</h4>'.format(result.error.message))
                
                self.response.write('<h3>error to dict</h3>')
                self.response.write('<pre class="prettyprint">{}</pre>'.format(result.error.to_dict()))
            
            elif result.user:
                response = result.user.update()
                if response:
                    self.response.write('<h3>User refresh status: {}</h3>'.format(response.status))
                    self.response.write('<pre class="prettyprint">{}</pre>'.format(response.content))
                    
                    self.response.write('<h3>Access-Control-Allow-Origin</h3>')
                    self.response.write('<pre class="prettyprint">{}</pre>'.format(response.getheader('Access-Control-Allow-Origin')))
                    
                    self.response.write('<h3>User headers</h3>')
                    self.response.write('<pre class="prettyprint">{}</pre>'.format(response.getheaders()))
                
                
                self.response.write('<h3>User</h3>')
                if result.user.picture:
                    self.response.write('<img src="{}" width="100" height="100" />'.format(result.user.picture))
                
                loop(self, result.user)
                
                if result.user.credentials:
                    # loop through credentials attrs
                    self.response.write('<h3>Credentials</h3>')
                    self.response.write('<h5>expiration time: {}</h5>'.format(result.user.credentials.expiration_time))
                    self.response.write('<h5>expiration date: {}</h5>'.format(result.user.credentials.expiration_date))
                    loop(self, result.user.credentials)
                    
                    self.response.write('<h3>Serialized credentials</h3>')
                    serialized_credentials = result.user.credentials.serialize()
                    endpoint_url = '/login/?type=elements&url=http://example.com&credentials=' + serialized_credentials
                    self.response.write('<a href="{}" target="_blank">{}</a>'.format(endpoint_url, serialized_credentials))
                    
                    json_input = """
                    {{"credentials": "{}",
                    "url": "http://example.com",
                    "method": "GET",
                    "params": {{"a": 1, "b": 2}},
                    "headers": {{"c": 3, "d": 4}}}}
                    """.format(result.user.credentials.serialize())
                    
                    self.response.write('<h3>JSON Request elements</h3>')
                    re = authomatic.request_elements(json_input=json_input, return_json=True)
                    self.response.write('<pre class="prettyprint">{}</pre>'.format(re))
                    
                    # refresh credentials
                    response = result.user.credentials.refresh(force=True)
                    
                    if response:
                        self.response.write('<h3>Refresh status: {}</h3>'.format(response.status))
                        self.response.write('<pre class="prettyprint">{}</pre>'.format(response.content))
                
                self.response.write('<pre id="ui" class="prettyprint">{}</pre>'.format(cgi.escape(result.user.content or '')))
                
                self.response.write("""
                <script type="text/javascript">
                    ui = document.getElementById('ui');
                    try {{
                        ui.innerHTML = JSON.stringify({0}, undefined, 4);
                    }} catch(e) {{
                        console.log('XML');
                    }}
                        
                </script>
                """.format(result.user.content.replace('\n', ' ')) if result.user.content else '')
            
            self.response.write('<h3>Result js callback HTML</h3>')
            self.response.write('<pre class="prettyprint">{}</pre>'\
                                .format(cgi.escape(result.popup_html('callback', indent=4,
                                                                      custom=dict(foo='bar', baz="bing")))))
                
            
            self.response.write('</body></html>')


class Home(webapp2.RequestHandler):
    def get(self):
        
        self.response.write('<h2>Number of providers: {}</h2>'.format(len(CONFIG)))
        
        links(self)
        


ROUTES = [webapp2.Route(r'/login/<:.*>', Login, handler_method='any'),
          webapp2.Route(r'/', Home)]

authomatic.setup(config=CONFIG, # Here goes the config.
                 secret='dsgdfgdgj5fd5g4fmjnfggf6gnkfgn5fngh4n564d3vr54er5',
                 report_errors=True,
                 logging_level=logging.DEBUG)

app = webapp2.WSGIApplication(ROUTES, debug=True)



