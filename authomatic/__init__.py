"""
This is the only interface that you should ever need to get **user info** and **credentials**
from a **provider** and to make asynchronous calls to their **protected resources**.

.. warning:: |async|

This is a simple webapp2 example:

::
     
    import webapp2
    import authomatic
    from authomatic.adapters import gaewebapp2
    
    # HTTP request handler
    class Login(webapp2.RequestHandler):
        
        # accept both GET and POST HTTP methods
        def anymethod(provider_name):
            
            # first we need platform adapter
            adapter = gaewebapp2.GAEWebapp2Adapter(self)
            
            # login by the provider
            result = authomatic.login(adapter, provider_name)
            
            if result:
                
                if result.error:
                    self.response.write('Login failed because {}!'.formar(result.error.message))
                elif result.user:
                    self.response.write('Hi {}!'.formar(result.user.name))
                    
                    if result.user.credentials:
                        # if there are credentials we can access user's protected resources
                       
                        # we can serialize store credentials to DB or elsewhere
                        sc = result.user.credentials.serialize()
                        
                        # we can test provider type
                        if result.user.credentials.provider_name == 'fb':
                            
                            # fetch multiple protected resources at once with serialized credentials
                            request1 = authomatic.async_fetch(adapter, sc,
                                                              'https://graph.facebook.com/me/og.follows',
                                                              method='GET').fetch() # returns immediately
                            request2 = authomatic.async_fetch(adapter, sc,
                                                              'https://graph.facebook.com/me/news.reads?' + \\
                                                              'article=http://example.com/article',
                                                              method='POST').fetch() # returns immediately
                            request3 = authomatic.async_fetch(adapter, sc,
                                                              'https://graph.facebook.com/me/video.watches?' + \\
                                                              'video=http://example.com/video',
                                                              method='POST').fetch() # returns immediately
                            
                            # they all now run in parallel
                            # so you can do other stuff while the requests fly through the Internet
                            
                            # collect results
                            response1 = request1.get_response() # returns when it has result
                            response2 = request2.get_response() # returns when it has result
                            response3 = request3.get_response() # returns when it has result

"""

from core import login, short_name, async_fetch, fetch