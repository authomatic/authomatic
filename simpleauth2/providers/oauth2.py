from simpleauth2 import providers
from simpleauth2.exceptions import CancellationError, FailureError, OAuth2Error
from urllib import urlencode
import logging
import simpleauth2.core as core


class OAuth2(providers.AuthorisationProvider):
    """
    Base class for OAuth2 services
    """
    
    #===========================================================================
    # Internal methods
    #===========================================================================
    
    @classmethod
    def _create_request_elements(cls, request_type, credentials, url, method='GET',
                                 redirect_uri='', scope='', state=''):
        
        consumer_key = credentials.consumer_key or ''
        consumer_secret = credentials.consumer_secret or ''
        token = credentials.token or ''
        
        # separate url base and query parameters
        url, base_params = cls._split_url(url)
        
        # add extracted params to future params
        params = dict(base_params)
        
        if request_type == cls.USER_AUTHORISATION_REQUEST_TYPE:
            # User authorisation request
            if consumer_key and redirect_uri and scope and state:
                # required
                params['client_id'] = consumer_key
                params['redirect_uri'] = redirect_uri
                params['scope'] = scope
                params['state'] = state
                params['response_type'] = 'code'
            else:
                raise OAuth2Error('Credentials with valid consumer_key and arguments redirect_uri, scope and ' + \
                                                         'state are required to create OAuth 2.0 user authorisation request elements!')
        
        elif request_type == cls.ACCESS_TOKEN_REQUEST_TYPE:
            # Access token request
            if token and consumer_key and consumer_secret and redirect_uri:
                params['code'] = token
                params['client_id'] = consumer_key
                params['client_secret'] = consumer_secret
                params['redirect_uri'] = redirect_uri
                params['grant_type'] = 'authorization_code'
            else:
                raise OAuth2Error('Credentials with valid token, consumer_key, consumer_secret and argument ' + \
                                                         'redirect_uri are required to create OAuth 2.0 acces token request elements!')
        
        elif request_type == cls.PROTECTED_RESOURCE_REQUEST_TYPE:
            # Protected resources request
            if token:
                params['access_token'] = token
            else:
                #TODO write error message
                raise OAuth2Error('Credentials with valid token are required to create ' + \
                                                         'OAuth 2.0 protected resources request elements!')
        
        params = urlencode(params)
        
        body = None
        
        if method in ('POST', 'PUT'):
            body = params
        else:
            url = url + '?' + params
        
        return url, body, method
        
    
    #===========================================================================
    # Exposed methods
    #===========================================================================
    
    @staticmethod
    def to_tuple(credentials):
        return (credentials.token, credentials.expiration_date)
    
    @classmethod
    def reconstruct(cls, deserialized_tuple, cfg):
        provider_short_name, token, expiration_date = deserialized_tuple
        
        return core.Credentials(token=token,
                                       provider_type=cls.get_type(),
                                       provider_short_name=provider_short_name,
                                       expiration_date=expiration_date)
    
    @classmethod
    def fetch_protected_resource(cls, adapter, url, credentials, content_parser, method='GET', headers={}, response_parser=None):
        # check required properties of credentials
        if not credentials.token:
            raise OAuth2Error('To access OAuth 2.0 resource you must provide credentials with valid token!')
        
        # NEW
        request_elements = cls._create_request_elements(request_type=cls.PROTECTED_RESOURCE_REQUEST_TYPE,
                                                       credentials=credentials,
                                                       url=url,
                                                       state=cls._generate_csrf())
        
        rpc = adapter.fetch_async(*request_elements,
                                    headers=headers,
                                    response_parser=response_parser,
                                    content_parser=content_parser)
        
        return rpc
    
    @providers._login_decorator
    def login(self, *args, **kwargs):
        
        credentials = core.Credentials(provider=self)
        
        # get request parameters from which we can determine the login phase
        authorisation_code = self.adapter.params.get('code')
        error = self.adapter.params.get('error')
        state = self.adapter.params.get('state')        
        
        if authorisation_code and state:
            # Phase 2 after redirect with success
            self._log(logging.INFO, 'Continuing OAuth 2.0 authorisation procedure after redirect.')
            
            # validate CSRF token
            self._log(logging.INFO, 'Validating request by comparing request state {} to stored state.'.format(state))
            stored_state = self._session_get('state')
            
            if not stored_state:
                raise FailureError('Unable to retrieve stored state!')
            elif not stored_state == state:
                raise FailureError('The returned state "{}" doesn\'t match with the stored state!'.format(state), url=self.urls[0])
            
            self._log(logging.INFO, 'Request is valid.')
            
            # exchange authorisation code for access token by the provider
            self._log(logging.INFO, 'Fetching access token from {}.'.format(self.access_token_url))
            
            credentials.token = authorisation_code
            
            request_elements = self._create_request_elements(request_type=self.ACCESS_TOKEN_REQUEST_TYPE,
                                                             credentials=credentials,
                                                             url=self.access_token_url,
                                                             method='POST',
                                                             redirect_uri=self.uri)
            
            response = self._fetch(*request_elements)
            
            access_token = response.data.get('access_token')
            
            if response.status_code != 200 or not access_token:
                raise FailureError('Failed to obtain OAuth access token from {}! HTTP status code: {}.'\
                                  .format(self.access_token_url, response.status_code),
                                  code=response.status_code,
                                  url=self.access_token_url)
            
            self._log(logging.INFO, 'Got access token.')            
            
            # OAuth 2.0 credentials need only access token and expires_in
            credentials.token = access_token
            credentials.expires_in = response.data.get('expires_in')
            # so we can reset these two guys
            credentials.consumer_key = None
            credentials.consumer_secret = None
            
            # update credentials
            credentials = self._credentials_parser(credentials, response.data)            
            
            # create user
            self._update_or_create_user(response.data, credentials)
            
            #===================================================================
            # We're done!
            #===================================================================
            
        elif error:
            # Phase 2 after redirect with error
            
            error_reason = self.adapter.params.get('error_reason')
            error_description = self.adapter.params.get('error_description')
            
            if error_reason == 'user_denied':
                raise CancellationError(error_description, url=self.user_authorisation_url)
            else:
                raise FailureError(error_description, url=self.user_authorisation_url)
            
        else:
            # phase 1 before redirect
            self._log(logging.INFO, 'Starting OAuth 2.0 authorisation procedure.')
            
            # generate csfr
            state = self._generate_csrf()
            # and store it to session
            self._session_set('state', state)
            
            request_elements = self._create_request_elements(request_type=self.USER_AUTHORISATION_REQUEST_TYPE,
                                                            credentials=credentials,
                                                            url=self.user_authorisation_url,
                                                            redirect_uri=self.uri,
                                                            scope=self._scope_parser(self.consumer.scope),
                                                            state=state)
            
            self._log(logging.INFO, 'Redirecting user to {}.'.format(request_elements[0]))
            
            self.adapter.redirect(request_elements[0])


class Facebook(OAuth2):
    """
    Facebook Oauth 2.0 service
    """
    
    user_authorisation_url = 'https://www.facebook.com/dialog/oauth'
    access_token_url = 'https://graph.facebook.com/oauth/access_token'
    user_info_url = 'https://graph.facebook.com/me'
    
    @staticmethod
    def _user_parser(user, data):
        user.user_id = data.get('id')
        user.picture = 'http://graph.facebook.com/{}/picture?type=large'.format(data.get('username'))
        return user
    
    
    @staticmethod
    def _credentials_parser(credentials, data):
        """
        We need to override this method to fix Facebooks naming deviation
        """
        
        # Facebook returns "expires" instead of "expires_in"
        credentials.expires_in = data.get('expires')
        return credentials


class Google(OAuth2):
    """
    Google Oauth 2.0 service
    """    
    
    user_authorisation_url = 'https://accounts.google.com/o/oauth2/auth'
    access_token_url = 'https://accounts.google.com/o/oauth2/token'
    user_info_url = 'https://www.googleapis.com/oauth2/v1/userinfo'
    
    @staticmethod
    def _user_parser(user, data):
        user.name = data.get('name')
        user.first_name = data.get('given_name')
        user.last_name = data.get('family_name')
        user.user_id = data.get('id')
        return user
    
    #TODO: rename to _parse_scope
    def _scope_parser(self, scope):
        """
        Google has space-separated scopes
        """
        return ' '.join(scope)
    
    
class WindowsLive(OAuth2):
    """
    Windlows Live Oauth 2.0 service
    """
    
    user_authorisation_url = 'https://oauth.live.com/authorize'
    access_token_url = 'https://oauth.live.com/token'
    user_info_url = 'https://apis.live.net/v5.0/me'
    
    @staticmethod
    def _user_parser(user, data):
        user.user_id = data.get('id')
        user.email = data.get('emails', {}).get('preferred')
        return user


