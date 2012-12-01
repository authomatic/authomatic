import webapp2
import webapp2_extras


class SessionRequestHandler(webapp2.RequestHandler):
    """
    Request handler with session
    """
    
    def dispatch(self):
        self.session_store = webapp2_extras.sessions.SessionStore(self.request, dict(secret_key='abcdefg'))
        
        try:
            super(SessionRequestHandler, self).dispatch()
        finally:
            # save sessions to session_store
            self.session_store.save_sessions(self.response)
    
    @webapp2.cached_property
    def session(self):
        """returns session from session store"""
        session = self.session_store.get_session(backend='datastore')
        return session