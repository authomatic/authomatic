from simpleauth2 import providers
from urllib import urlencode
import simpleauth2


class OAuth2(providers.BaseProvider):
    """
    Base class for OAuth2 services
    """
    
    @staticmethod
    def credentials_to_tuple(credentials):
        return (credentials.access_token, credentials.expiration_date)
    
    @classmethod
    def credentials_from_tuple(cls, tuple_):
        short_name, access_token, expiration_date = tuple_
        return simpleauth2.Credentials(access_token, cls.get_type(), short_name, expiration_date=expiration_date)
    
    @classmethod
    def fetch_protected_resource(cls, adapter, url, credentials, content_parser, method='GET', response_parser=None):
        # check required properties of credentials
        if not credentials.access_token:
            raise simpleauth2.exceptions.OAuth2Error('To access OAuth 2.0 resource you must provide credentials with valid access_token!')
        
        url2 = cls.create_url(2, url, access_token=credentials.access_token)
        
        rpc = adapter.fetch_async(content_parser,
                                  url=url2,
                                  response_parser=response_parser)
        
        return rpc
    
    
    @staticmethod
    def create_url(url_type, base, consumer_key=None, access_token=None, redirect_uri=None, scope=None, state=None):
        
        params = {}
        
        if url_type == 1:
            # Authorization Request http://tools.ietf.org/html/draft-ietf-oauth-v2-31#section-4.1.1
            if consumer_key:
                # required
                params['client_id'] = consumer_key
                params['response_type'] = 'code'
                
                # optional
                if redirect_uri: params['redirect_uri'] = redirect_uri
                if scope: params['scope'] = scope
                if state: params['state'] = state
            else:
                raise simpleauth2.exceptions.OAuth2Error('Parameter consumer_key is required to create Authorization Requestn URL!')
        
        if url_type == 2:
            # 
            if access_token:
                params['access_token'] = access_token
            else:
                raise simpleauth2.exceptions.OAuth2Error('')
            
        return base + '?' + urlencode(params)
     
    def login(self):
        
        self._check_consumer()
        
        if self.phase == 0:
            
            self._increase_phase()
            
            # generate csfr
            csrf_token = self.adapter.generate_csrf()
            self.adapter.store_provider_data(self.provider_name, 'csrf_token', csrf_token)
            
            url = self.create_url(1, self.urls[0],
                                    consumer_key=self.consumer.key,
                                    redirect_uri=self.uri,
                                    scope=self._normalize_scope(self.consumer.scope),
                                    state=csrf_token)
            
            self.adapter.redirect(url)
            
        if self.phase == 1:
            
            # Validate CSRF token
            csrf_token = self.adapter.retrieve_provider_data(self.provider_name, 'csrf_token')
            state = self.adapter.get_request_param('state')
            if not csrf_token == state:
                raise simpleauth2.exceptions.CSRFError("The value {} of the \"state\" parameter returned by the provider doesn't match with the saved CSRF token!".format(state))
            
            # check access token
            self.consumer.access_token = self.adapter.get_request_param('code')
            if not self.consumer.access_token:
                self.adapter.reset_phase(self.provider_name)
                raise Exception('Failed to get access token from provider {}!'.format(self.provider_name))
            
            # exchange authorisation code for access token by the provider
            # the parameters should be encoded in the headers so create_oauth2_url() doesn't help
            params = dict(code=self.consumer.access_token,
                          client_id=self.consumer.key,
                          client_secret=self.consumer.secret,
                          redirect_uri=self.uri,
                          grant_type='authorization_code')
            
            parser = self._get_parser_by_index(1)
            response = self._fetch(parser, self.urls[1], params, 'POST', headers={'Content-Type': 'application/x-www-form-urlencoded'})
                        
            # create user
            self._update_or_create_user(response.data)
            
            # create credentials
            self.credentials = simpleauth2.Credentials(response.data.get('access_token'), self.get_type(), self.short_name)
            self._update_credentials(response.data)
            
            # create event
            event = simpleauth2.AuthEvent(self, self.consumer, self.user, self.credentials)
            
            # reset phase
            self.adapter.reset_phase(self.provider_name)
            
            # call callback with event
            self.callback(event)


class Facebook(OAuth2):
    """
    Facebook Oauth 2.0 service
    """
    
    # class properties
    urls = ('https://www.facebook.com/dialog/oauth',
            'https://graph.facebook.com/oauth/access_token',
            'https://graph.facebook.com/me')
    
    parsers = (None, providers.QUERY_STRING_PARSER)
    
    user_info_mapping = dict(user_id='short_name',
                            picture=(lambda data: 'http://graph.facebook.com/{}/picture?type=large'.format(data.get('username'))))
    
    def _update_credentials(self, data):
        """
        We need to override this method to fix Facebooks naming deviation
        """
        credentials = super(Facebook, self)._update_credentials(data)
        
        # Facebook returns "expires" instead of "expires_in"
        credentials.expires_in = data.get('expires')
        return credentials


class Google(OAuth2):
    """
    Google Oauth 2.0 service
    """
    
    # class properties
    urls = ('https://accounts.google.com/o/oauth2/auth',
            'https://accounts.google.com/o/oauth2/token',
            'https://www.googleapis.com/oauth2/v1/userinfo')
    
    parsers = (None, providers.JSON_PARSER)
    
    user_info_mapping = dict(name='name',
                            first_name='given_name',
                            last_name='family_name',
                            user_id='short_name')
    
    def _normalize_scope(self, scope):
        """
        Google has space-separated scopes
        """
        return ' '.join(scope)
    
    
class WindowsLive(OAuth2):
    """
    Windlows Live Oauth 2.0 service
    """
    
    # class properties
    urls = ('https://oauth.live.com/authorize',
            'https://oauth.live.com/token',
            'https://apis.live.net/v5.0/me')
    
    parsers = (None, providers.JSON_PARSER)
    
    user_info_mapping=dict(user_id='short_name',
                           email=(lambda data: data.get('emails', {}).get('preferred')))