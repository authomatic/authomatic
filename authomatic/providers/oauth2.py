"""
OAuth 2.0 Providers
-------------------

Providers which implement the |oauth2|_ protocol.

.. autosummary::
    
    Facebook
    Google
    WindowsLive
    OAuth2
    
"""

from authomatic import providers
from authomatic.exceptions import CancellationError, FailureError, OAuth2Error
from urllib import urlencode
import logging
import authomatic.core as core

__all__ = ['Facebook', 'Google', 'WindowsLive', 'OAuth2']

class OAuth2(providers.AuthorisationProvider):
    """
    Base class for |oauth2|_ providers.
    """
    
    # I intruduced this dictionary because of Facebook,
    # who likes to invent its own terminology for OAuth 2.0!!!
    _term_dict = dict(refresh_token='refresh_token',
                      authorization_code='authorization_code',
                      password='password',  
                      client_credentials='client_credentials')
    
    def __init__(self, *args, **kwargs):
        """
        Accepts additional keyword arguments:
        
        :param list scope:
            List of strings specifying requested permissions as described in the
            `OAuth 2.0 spec <http://tools.ietf.org/html/rfc6749#section-3.3>`_.
        
        As well as those inherited from :class:`.AuthorisationProvider` constructor.
        """
        
        super(OAuth2, self).__init__(*args, **kwargs)
        
        self.scope = self._kwarg(kwargs, 'scope', [])
    
    
    #===========================================================================
    # Internal methods
    #===========================================================================
    
    
    def _scope_parser(self, scope):
        """
        Override this to handle differences between accepted format of scope across different providers.
        
        :attr list scope:
            List of scopes.
        """
        
        # Most providers accept csv scope.
        return ','.join(scope) if scope else ''
    
    
    @classmethod
    def _create_request_elements(cls, request_type, credentials, url, method='GET',
                                 redirect_uri='', scope='', csrf='', params={}):
        
        consumer_key = credentials.consumer_key or ''
        consumer_secret = credentials.consumer_secret or ''
        token = credentials.token or ''
        refresh_token = credentials.refresh_token or credentials.token or ''
        
        
        
        # Separate url base and query parameters.
        url, base_params = cls._split_url(url)
        
        params
        
        # Add params extracted from URL.
        params.update(dict(base_params))
        
        if request_type == cls.USER_AUTHORISATION_REQUEST_TYPE:
            # User authorisation request.
            if consumer_key and redirect_uri and scope and csrf:
                params['client_id'] = consumer_key
                params['redirect_uri'] = redirect_uri
                params['scope'] = scope
                params['state'] = csrf
                params['response_type'] = 'code'
            else:
                raise OAuth2Error('Credentials with valid consumer_key and arguments redirect_uri, scope and ' + \
                                  'state are required to create OAuth 2.0 user authorisation request elements!')
        
        elif request_type == cls.ACCESS_TOKEN_REQUEST_TYPE:
            # Access token request.
            if token and consumer_key and consumer_secret and redirect_uri:
                params['code'] = token
                params['client_id'] = consumer_key
                params['client_secret'] = consumer_secret
                params['redirect_uri'] = redirect_uri
                params['grant_type'] = cls._term_dict['authorization_code']
            else:
                raise OAuth2Error('Credentials with valid token, consumer_key, consumer_secret and argument ' + \
                                  'redirect_uri are required to create OAuth 2.0 acces token request elements!')
        
        elif request_type == cls.REFRESH_TOKEN_REQUEST_TYPE:
            # Access token request.
            if refresh_token and consumer_key and consumer_secret:
                params[cls._term_dict['refresh_token']] = refresh_token
                params['client_id'] = consumer_key
                params['client_secret'] = consumer_secret
                params['grant_type'] = cls._term_dict['refresh_token']
            else:
                raise OAuth2Error('Credentials with valid refresh_token, consumer_key, consumer_secret ' + \
                                  'are required to create OAuth 2.0 refresh token request elements!')
        
        elif request_type == cls.PROTECTED_RESOURCE_REQUEST_TYPE:
            # Protected resource request.
            if token:
                params['access_token'] = token
            else:
                raise OAuth2Error('Credentials with valid token are required to create ' + \
                                  'OAuth 2.0 protected resources request elements!')
        
        params = urlencode(params)
        
        body = None
        
        if method in ('POST', 'PUT'):
            # Send params in the body
            body = params
        else:
            # Send params as query string
            url = url + '?' + params
        
        return url, body, method
    
    
    @staticmethod
    def _refresh_credentials_if(credentials):
        """
        Override this to specify conditions when it is worth to refresh credentials.
        
        .. warning:: |classmethod|
        
        :param credentials:
            :class:`.Credentials`
        
        :returns:
            ``True`` or ``False``
        """
        
        return True
    
    
    #===========================================================================
    # Exposed methods
    #===========================================================================
    
    @staticmethod
    def to_tuple(credentials):
        
        # OAuth 2.0 needs only token, refresh_token and expiration date.
        return (credentials.token, credentials.refresh_token, credentials.expiration_date)
    
    
    @classmethod
    def reconstruct(cls, deserialized_tuple, cfg):
        
        provider_short_name, token, refresh_token, expiration_date = deserialized_tuple
        
        return core.Credentials(token=token,
                                refresh_token=refresh_token,
                                provider_type=cls.get_type(),
                                provider_short_name=provider_short_name,
                                expiration_date=expiration_date,
                                provider_class=cls)
    
    
    @classmethod
    def refresh_credentials(cls, adapter, config, credentials):
        """
        Refreshes :class:`.Credentials` by providing fresh **token**,
        **refresh_token** and **expires_in**.
        
        :param adapter:
            :doc:`Adapter <adapters>`
        :param credentials:
            :class:`.Credentials`
        
        :returns:
            :class:`.Response`.
        """
        
        if not cls._refresh_credentials_if(credentials):
            return
        
        # We need consumer key and secret to make this kind of request.
        cfg = config.get(credentials.provider_name)
        credentials.consumer_key = cfg.get('consumer_key')
        credentials.consumer_secret = cfg.get('consumer_secret')
        
        request_elements = cls._create_request_elements(request_type=cls.REFRESH_TOKEN_REQUEST_TYPE,
                                                        credentials=credentials,
                                                        url=cls.access_token_url,
                                                        method='POST')
        
        response = adapter.fetch_async(*request_elements).get_response()
        
        # We no longer need consumer info.
        credentials.consumer_key = None
        credentials.consumer_secret = None
        
        # Extract the refreshed data.
        access_token = response.data.get('access_token')
        refresh_token = response.data.get('refresh_token')
        
        # Update credentials only if there is access token.
        if access_token:
            credentials.token = access_token
            credentials.expires_in = response.data.get('expires_in')
            
            # Update refresh token only if there is a new one.
            if refresh_token:
                credentials.refresh_token = refresh_token
            
            # Handle different naming conventions across providers.
            credentials = cls._credentials_parser(credentials, response.data)
        
        return response
    
    
    @providers.login_decorator
    def login(self):
        
        # get request parameters from which we can determine the login phase
        
        authorisation_code = core.mw.params.get('code')
        error = core.mw.params.get('error')
        state = core.mw.params.get('state')      
        
        if authorisation_code and state:
            #===================================================================
            # Phase 2 after redirect with success
            #===================================================================
            
            self._log(logging.INFO, 'Continuing OAuth 2.0 authorisation procedure after redirect.')
            
            # validate CSRF token
            self._log(logging.INFO, 'Validating request by comparing request state {} to stored state.'.format(state))
            stored_state = self._session_get('state')
            
            if not stored_state:
                raise FailureError('Unable to retrieve stored state!')
            elif not stored_state == state:
                raise FailureError('The returned state "{}" doesn\'t match with the stored state!'.format(state),
                                   url=self.user_authorisation_url)
            
            self._log(logging.INFO, 'Request is valid.')
            
            # exchange authorisation code for access token by the provider
            self._log(logging.INFO, 'Fetching access token from {}.'.format(self.access_token_url))
            
            self.credentials.token = authorisation_code
            
            request_elements = self._create_request_elements(request_type=self.ACCESS_TOKEN_REQUEST_TYPE,
                                                             credentials=self.credentials,
                                                             url=self.access_token_url,
                                                             method='POST',
                                                             redirect_uri=core.mw.url,
                                                             params=self.access_token_params)
            
            response = self._new_fetch(*request_elements)
            
            access_token = response.data.get('access_token')
            refresh_token = response.data.get('refresh_token')
            
            if response.status_code != 200 or not access_token:
                raise FailureError('Failed to obtain OAuth 2.0 access token from {}! HTTP status code: {}.'\
                                  .format(self.access_token_url, response.status_code),
                                  original_message=response.content,
                                  code=response.status_code,
                                  url=self.access_token_url)
            
            self._log(logging.INFO, 'Got access token.')
            
            if refresh_token:
                self._log(logging.INFO, 'Got refresh access token.')
            
            # OAuth 2.0 credentials need only access token, refresh token and expires_in.
            self.credentials.token = access_token
            self.credentials.refresh_token = refresh_token
            self.credentials.expires_in = response.data.get('expires_in')
            # so we can reset these two guys
            self.credentials.consumer_key = None
            self.credentials.consumer_secret = None
            
            # update credentials
            self.credentials = self._credentials_parser(self.credentials, response.data)            
            
            # create user
            self._update_or_create_user(response.data, self.credentials)
            
            #===================================================================
            # We're done!
            #===================================================================
            
        elif error:
            #===================================================================
            # Phase 2 after redirect with error
            #===================================================================
            
            error_reason = core.mw.params.get('error_reason')
            error_description = core.mw.params.get('error_description')
            
            if error_reason == 'user_denied':
                raise CancellationError(error_description, url=self.user_authorisation_url)
            else:
                raise FailureError(error_description, url=self.user_authorisation_url)
            
        else:
            #===================================================================
            # Phase 1 before redirect
            #===================================================================
            
            self._log(logging.INFO, 'Starting OAuth 2.0 authorisation procedure.')
            
            # generate csfr
            csrf = self.csrf_generator()
            # and store it to session
            self._session_set('state', csrf)
                        
            request_elements = self._create_request_elements(request_type=self.USER_AUTHORISATION_REQUEST_TYPE,
                                                            credentials=self.credentials,
                                                            url=self.user_authorisation_url,
                                                            redirect_uri=core.mw.url,
                                                            scope=self._scope_parser(self.scope),
                                                            csrf=csrf,
                                                            params=self.user_authorisation_params)
            
            self._log(logging.INFO, 'Redirecting user to {}.'.format(request_elements[0]))
            
            core.mw.redirect(request_elements[0])


class Facebook(OAuth2):
    """Facebook |oauth2|_ provider."""
    
    user_authorisation_url = 'https://www.facebook.com/dialog/oauth'
    access_token_url = 'https://graph.facebook.com/oauth/access_token'
    user_info_url = 'https://graph.facebook.com/me'
    
    # Facebook is original as usual and has its own name for "refresh_token"!!!
    _term_dict = OAuth2._term_dict.copy()
    _term_dict['refresh_token'] = 'fb_exchange_token'
    
    @staticmethod
    def _user_parser(user, data):
        user.picture = 'http://graph.facebook.com/{}/picture?type=large'.format(data.get('username'))
        return user
        
    @staticmethod
    def _credentials_parser(credentials, data):
        """
        We need to override this method to fix Facebooks naming deviation.
        """
        
        # Facebook returns "expires" instead of "expires_in".
        credentials.expires_in = data.get('expires')
        
        return credentials


class Google(OAuth2):
    """Google |oauth2|_ provider."""
    
    user_authorisation_url = 'https://accounts.google.com/o/oauth2/auth'
    access_token_url = 'https://accounts.google.com/o/oauth2/token'
    user_info_url = 'https://www.googleapis.com/oauth2/v1/userinfo'
    
    
    @staticmethod
    def _refresh_credentials_if(credentials):
        # Refres credentials only if there is refresh_token.
        return credentials.refresh_token
    
    
    @staticmethod
    def _user_parser(user, data):
        user.name = data.get('name')
        user.first_name = data.get('given_name')
        user.last_name = data.get('family_name')
        return user
    
    
    def _scope_parser(self, scope):
        """
        Google has space-separated scopes
        """
        return ' '.join(scope)
    
    
class WindowsLive(OAuth2):
    """Windows Live |oauth2|_ provider."""
    
    user_authorisation_url = 'https://oauth.live.com/authorize'
    access_token_url = 'https://oauth.live.com/token'
    user_info_url = 'https://apis.live.net/v5.0/me'
    
    @staticmethod
    def _user_parser(user, data):
        user.email = data.get('emails', {}).get('preferred')
        return user


