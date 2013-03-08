# -*- coding: utf-8 -*-
"""
|oauth2| Providers
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
import authomatic.core as core
import authomatic.settings as settings
import base64
import logging


__all__ = ['OAuth2', 'Bitly', 'Cosm', 'DeviantART', 'Facebook', 'Foursquare', 'Google', 'Reddit',
           'Viadeo', 'WindowsLive']


class OAuth2(providers.AuthorisationProvider):
    """
    Base class for |oauth2|_ providers.
    """
    
    TOKEN_TYPES = ['', 'Bearer']
    
    # I intruduced this dictionary because of Facebook,
    # who likes to invent its own terminology for OAuth 2.0!!!
    _x_term_dict = dict(refresh_token='refresh_token',
                        authorization_code='authorization_code',
                        password='password',
                        client_credentials='client_credentials',
                        access_token='access_token')
    
    #: A scope preset to get most of the **user** info.
    #: Use it in the :doc:`config` like ``{'scope': oauth2.Facebook.user_info_scope}``.
    user_info_scope = []
    
    #: :class:`bool` If ``False``, the provider doesn't support CSRF protection.
    supports_csrf_protection = True
    
    def __init__(self, *args, **kwargs):
        """
        Accepts additional keyword arguments:
        
        :param list scope:
            List of strings specifying requested permissions as described in the
            `OAuth 2.0 spec <http://tools.ietf.org/html/rfc6749#section-3.3>`_.
        
        :param bool offline:
            If ``True`` the **provider** will be set up to request an *offline access token*.
            default is ``False``.
        
        As well as those inherited from :class:`.AuthorisationProvider` constructor.
        """
        
        super(OAuth2, self).__init__(*args, **kwargs)
        
        self.scope = self._kwarg(kwargs, 'scope', [])
        self.offline = self._kwarg(kwargs, 'offline', False)
    
    
    #===========================================================================
    # Internal methods
    #===========================================================================
    
    def _x_scope_parser(self, scope):
        """
        Override this to handle differences between accepted format of scope across providers.
        
        :attr list scope:
            List of scopes.
        """
        
        # Most providers accept csv scope.
        return ','.join(scope) if scope else ''
    
    
    @classmethod
    def _create_request_elements(cls, request_type, credentials, url, params=None,
                                 method='GET', redirect_uri='', scope='', csrf=''):
        """
        Creates |oauth2| request elements.
        """
        
        params = params or {}
        
        consumer_key = credentials.consumer_key or ''
        consumer_secret = credentials.consumer_secret or ''
        token = credentials.token or ''
        refresh_token = credentials.refresh_token or credentials.token or ''
        
        # Separate url base and query parameters.
        url, base_params = cls._split_url(url)
                
        # Add params extracted from URL.
        params.update(dict(base_params))
        
        if request_type == cls.USER_AUTHORISATION_REQUEST_TYPE:
            # User authorisation request.
            if consumer_key and redirect_uri and (csrf or not cls.supports_csrf_protection):
                params['client_id'] = consumer_key
                params['redirect_uri'] = redirect_uri
                params['scope'] = scope
                params['state'] = csrf or cls.csrf_generator()
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
                params['grant_type'] = cls._x_term_dict['authorization_code']
            else:
                raise OAuth2Error('Credentials with valid token, consumer_key, consumer_secret and argument ' + \
                                  'redirect_uri are required to create OAuth 2.0 acces token request elements!')
        
        elif request_type == cls.REFRESH_TOKEN_REQUEST_TYPE:
            # Refresh access token request.
            if refresh_token and consumer_key and consumer_secret:
                params[cls._x_term_dict['refresh_token']] = refresh_token
                params['client_id'] = consumer_key
                params['client_secret'] = consumer_secret
                params['grant_type'] = cls._x_term_dict['refresh_token']
            else:
                raise OAuth2Error('Credentials with valid refresh_token, consumer_key, consumer_secret ' + \
                                  'are required to create OAuth 2.0 refresh token request elements!')
        
        elif request_type == cls.PROTECTED_RESOURCE_REQUEST_TYPE:
            # Protected resource request.
            if credentials.token_type == cls.BEARER:
                pass
            elif token:
                params[cls._x_term_dict['access_token']] = token
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
    def _x_refresh_credentials_if(credentials):
        """
        Override this to specify conditions when it gives sense to refresh credentials.
        
        .. warning:: |classmethod|
        
        :param credentials:
            :class:`.Credentials`
        
        :returns:
            ``True`` or ``False``
        """
        
        if credentials.refresh_token:
            return True
    
    
    #===========================================================================
    # Exposed methods
    #===========================================================================
    
    
    @classmethod
    def to_tuple(cls, credentials):
        return (credentials.token,
                credentials.refresh_token,
                credentials.expiration_time,
                cls.TOKEN_TYPES.index(credentials.token_type))
    
    
    @classmethod
    def reconstruct(cls, deserialized_tuple, cfg):
        provider_id, token, refresh_token, expiration_time, token_type = deserialized_tuple
        return core.Credentials(token=token,
                                refresh_token=refresh_token,
                                provider_type=cls.get_type(),
                                provider_id=provider_id,
                                expiration_time=expiration_time,
                                provider_class=cls,
                                token_type=cls.TOKEN_TYPES[token_type])
    
    
    @classmethod
    def refresh_credentials(cls, credentials):
        """
        Refreshes :class:`.Credentials` if it gives sense.
        
        :param credentials:
            :class:`.Credentials` to be refreshed.
        
        :returns:
            :class:`.Response`.
        """
        
        if not cls._x_refresh_credentials_if(credentials):
            return
        
        # We need consumer key and secret to make this kind of request.
        cfg = settings.config.get(credentials.provider_name)
        credentials.consumer_key = cfg.get('consumer_key')
        credentials.consumer_secret = cfg.get('consumer_secret')
        
        request_elements = cls._create_request_elements(request_type=cls.REFRESH_TOKEN_REQUEST_TYPE,
                                                        credentials=credentials,
                                                        url=cls.access_token_url,
                                                        method='POST')
        
        cls._log(logging.INFO, 'Refreshing credentials.')
        response = cls._fetch(*request_elements,
                              headers=cls._authorisation_header(credentials))
        
        # We no longer need consumer info.
        credentials.consumer_key = None
        credentials.consumer_secret = None
        
        # Extract the refreshed data.
        access_token = response.data.get('access_token')
        refresh_token = response.data.get('refresh_token')
        
        # Update credentials only if there is access token.
        if access_token:
            credentials.token = access_token
            credentials.expire_in = response.data.get('expire_in')
            
            # Update refresh token only if there is a new one.
            if refresh_token:
                credentials.refresh_token = refresh_token
            
            # Handle different naming conventions across providers.
            credentials = cls._x_credentials_parser(credentials, response.data)
        
        return response
    
    
    @providers.login_decorator
    def login(self):
        
        # get request parameters from which we can determine the login phase
        authorisation_code = core.middleware.params.get('code')
        error = core.middleware.params.get('error')
        state = core.middleware.params.get('state')      
        
#        if authorisation_code and state:
        if authorisation_code:
            #===================================================================
            # Phase 2 after redirect with success
            #===================================================================
            
            self._log(logging.INFO, 'Continuing OAuth 2.0 authorisation procedure after redirect.')
            
            # validate CSRF token
            if self.supports_csrf_protection:
                self._log(logging.INFO, 'Validating request by comparing request state with stored state.')
                stored_state = self._session_get('state')
                
                if not stored_state:
                    raise FailureError('Unable to retrieve stored state!')
                elif not stored_state == state:
                    raise FailureError('The returned state "{}" doesn\'t match with the stored state!'.format(state),
                                       url=self.user_authorisation_url)
                self._log(logging.INFO, 'Request is valid.')
            else:
                self._log(logging.WARN, 'Skipping CSRF validation!')
            
            # exchange authorisation code for access token by the provider
            self._log(logging.INFO, 'Fetching access token from {}.'.format(self.access_token_url))
            
            self.credentials.token = authorisation_code
            
            request_elements = self._create_request_elements(request_type=self.ACCESS_TOKEN_REQUEST_TYPE,
                                                             credentials=self.credentials,
                                                             url=self.access_token_url,
                                                             method='POST',
                                                             redirect_uri=core.middleware.url,
                                                             params=self.access_token_params)
            
            # Add Authorisation headers.
            self.access_token_headers.update(self._authorisation_header(self.credentials))
            
            response = self._fetch(*request_elements,
                                   headers=self.access_token_headers)
            
            access_token = response.data.get('access_token', '')
            refresh_token = response.data.get('refresh_token', '')
            
            if response.status != 200 or not access_token:
                raise FailureError('Failed to obtain OAuth 2.0 access token from {}! HTTP status: {}, message: {}.'\
                                  .format(self.access_token_url, response.status, response.content),
                                  original_message=response.content,
                                  status=response.status,
                                  url=self.access_token_url)
            
            self._log(logging.INFO, 'Got access token.')
            
            if refresh_token:
                self._log(logging.INFO, 'Got refresh access token.')
            
            # OAuth 2.0 credentials need only access token, refresh token and expire_in.
            self.credentials.token = access_token
            self.credentials.refresh_token = refresh_token
            self.credentials.expire_in = response.data.get('expire_in')
            self.credentials.token_type = response.data.get('token_type', '')
            # so we can reset these two guys
            self.credentials.consumer_key = ''
            self.credentials.consumer_secret = ''
            
            # update credentials
            self.credentials = self._x_credentials_parser(self.credentials, response.data)            
            
            # create user
            self._update_or_create_user(response.data, self.credentials)
            
            #===================================================================
            # We're done!
            #===================================================================
            
        elif error:
            #===================================================================
            # Phase 2 after redirect with error
            #===================================================================
            
            error_reason = core.middleware.params.get('error_reason')
            error_description = core.middleware.params.get('error_description')
            
            if error_reason == 'user_denied':
                raise CancellationError(error_description, url=self.user_authorisation_url)
            else:
                raise FailureError(error_description, url=self.user_authorisation_url)
            
        else:
            #===================================================================
            # Phase 1 before redirect
            #===================================================================
            
            self._log(logging.INFO, 'Starting OAuth 2.0 authorisation procedure.')
            
            csrf = ''
            if self.supports_csrf_protection:
                # generate csfr
                csrf = self.csrf_generator()
                # and store it to session
                self._session_set('state', csrf)
            else:
                self._log(logging.WARN, 'Provider doesn\'t support CSRF validation!')
                        
            request_elements = self._create_request_elements(request_type=self.USER_AUTHORISATION_REQUEST_TYPE,
                                                            credentials=self.credentials,
                                                            url=self.user_authorisation_url,
                                                            redirect_uri=core.middleware.url,
                                                            scope=self._x_scope_parser(self.scope),
                                                            csrf=csrf,
                                                            params=self.user_authorisation_params)
            
            self._log(logging.INFO, 'Redirecting user to {}.'.format(request_elements[0]))
            
            core.middleware.redirect(request_elements[0])


class Bitly(OAuth2):
    """
    Bitly |oauth2|_ provider.
    
    .. warning::
        
        |no-csrf|
    
    * Dashboard: http://dev.bitly.com/my_apps.html
    * Docs: http://dev.bitly.com/authentication.html
    * API reference: http://dev.bitly.com/api.html
    """
    
    supports_csrf_protection = False
    _x_use_authorisation_header = False
    
    user_authorisation_url = 'https://bitly.com/oauth/authorize'
    access_token_url = 'https://api-ssl.bitly.com/oauth/access_token'
    user_info_url = 'https://api-ssl.bitly.com/v3/user/info'
    
    def __init__(self, *args, **kwargs):
        super(Bitly, self).__init__(*args, **kwargs)
        
        if self.offline:
            if not 'grant_type' in self.access_token_params:
                self.access_token_params['grant_type'] = 'refresh_token'
    
    @staticmethod
    def _x_user_parser(user, data):
        info = data.get('data', {})
        
        user.id = info.get('login')
        user.name = info.get('full_name')
        user.username = info.get('display_name')
        user.picture = info.get('profile_image')
        user.link = info.get('profile_url')
        
        return user


class Cosm(OAuth2):
    """
    Cosm |oauth2|_ provider.
    
    .. note::
        
        Cosm doesn't provide any *user info URL*.
    
    * Dashboard: https://cosm.com/users/peterhudec/apps
    * Docs: https://cosm.com/docs/
    * API reference: https://cosm.com/docs/v2/
    """
    
    user_authorisation_url = 'https://cosm.com/oauth/authenticate'
    access_token_url = 'https://cosm.com/oauth/token'
    user_info_url = ''
    
    @staticmethod
    def _x_user_parser(user, data):
        user.id = user.username = data.get('user')
        return user


class DeviantART(OAuth2):
    """
    DeviantART |oauth2|_ provider.
    
    * Dashboard: https://www.deviantart.com/settings/myapps
    * Docs: http://www.deviantart.com/developers/oauth2
    * API reference: http://www.deviantart.com/developers/oauth2
    """
    
    user_authorisation_url = 'https://www.deviantart.com/oauth2/draft15/authorize'
    access_token_url = 'https://www.deviantart.com/oauth2/draft15/token'
    user_info_url = 'https://www.deviantart.com/api/draft15/user/whoami'
    
    def __init__(self, *args, **kwargs):
        super(DeviantART, self).__init__(*args, **kwargs)
        
        if self.offline:
            if not 'grant_type' in self.access_token_params:
                self.access_token_params['grant_type'] = 'refresh_token'
    
    
    @staticmethod
    def _x_user_parser(user, data):
        user.picture = data.get('usericonurl')
        return user


class Facebook(OAuth2):
    """
    Facebook |oauth2|_ provider.
    
    * Dashboard: https://developers.facebook.com/apps
    * Docs: http://developers.facebook.com/docs/howtos/login/server-side-login/
    * API reference: http://developers.facebook.com/docs/reference/api/
    * API explorer: http://developers.facebook.com/tools/explorer
    """
    
    user_authorisation_url = 'https://www.facebook.com/dialog/oauth'
    access_token_url = 'https://graph.facebook.com/oauth/access_token'
    user_info_url = 'https://graph.facebook.com/me'
    
    user_info_scope = ['user_about_me', 'email']
    
    # Facebook is original as usual and has its own name for "refresh_token"!!!
    _x_term_dict = OAuth2._x_term_dict.copy()
    _x_term_dict['refresh_token'] = 'fb_exchange_token'
    
    
    def __init__(self, *args, **kwargs):
        super(Facebook, self).__init__(*args, **kwargs)
        
        # Handle special Facebook requirements to be able to refresh the access token.
        if self.offline:
            # Facebook needs an offline_access scope.
            if not 'offline_access' in self.scope:
                self.scope.append('offline_access')
    
    
    @staticmethod
    def _x_user_parser(user, data):
        user.picture = 'http://graph.facebook.com/{}/picture?type=large'.format(data.get('username'))
        return user
    
    
    @staticmethod
    def _x_credentials_parser(credentials, data):
        """
        We need to override this method to fix Facebooks naming deviation.
        """
        
        # Facebook returns "expires" instead of "expire_in".
        credentials.expire_in = data.get('expires')
        
        return credentials
    
    
    @staticmethod
    def _x_refresh_credentials_if(credentials):
        # Allways refresh.
        return True


class Foursquare(OAuth2):
    """
    Foursquare |oauth2|_ provider.
    
    * Dashboard: https://foursquare.com/developers/apps
    * Docs: https://developer.foursquare.com/overview/auth.html
    * API reference: https://developer.foursquare.com/docs/
    """
    
    # Foursquare uses OAuth 1.0 "oauth_token" for what should be "access_token" in OAuth 2.0!
    _x_term_dict = OAuth2._x_term_dict.copy()
    _x_term_dict['access_token'] = 'oauth_token'
    
    user_authorisation_url = 'https://foursquare.com/oauth2/authenticate'
    access_token_url = 'https://foursquare.com/oauth2/access_token'
    user_info_url = 'https://api.foursquare.com/v2/users/self'
    
    @staticmethod
    def _x_user_parser(user, data):
        
        _resp = data.get('response', {})
        _user = _resp.get('user', {})
        
        user.id = _user.get('id')
        user.first_name = _user.get('firstName')
        user.last_name = _user.get('lastName')
        user.gender = _user.get('gender')
        user.picture = _user.get('photo')
        
        user.city, user.country = _user.get('homeCity', ', ').split(', ')
        
        _contact = _user.get('contact', {})
        user.email = _contact.get('email')
        user.phone = _contact.get('phone')
        
        return user


class GitHub(OAuth2):
    """
    GitHub |oauth2|_ provider.
    
    * Dashboard: https://github.com/settings/applications/
    * Docs: http://developer.github.com/v3/#authentication
    * API reference: http://developer.github.com/v3/
    """
    
    user_authorisation_url = 'https://github.com/login/oauth/authorize'
    access_token_url = 'https://github.com/login/oauth/access_token'
    user_info_url = 'https://api.github.com/user'
    
    @staticmethod
    def _x_user_parser(user, data):
        user.username = data.get('login')
        user.picture = data.get('avatar_url')
        user.link = data.get('html_url')
        user.city, user.country = data.get('location', ', ').split(', ')
        return user


class Google(OAuth2):
    """
    Google |oauth2|_ provider.
    
    * Dashboard: https://code.google.com/apis/console/
    * Docs: https://developers.google.com/accounts/docs/OAuth2
    * API reference: https://developers.google.com/gdata/docs/directory
    * API explorer: https://developers.google.com/oauthplayground/
    """
    
    user_authorisation_url = 'https://accounts.google.com/o/oauth2/auth'
    access_token_url = 'https://accounts.google.com/o/oauth2/token'
    user_info_url = 'https://www.googleapis.com/oauth2/v1/userinfo'
    
    user_info_scope = ['https://www.googleapis.com/auth/userinfo.profile',
                       'https://www.googleapis.com/auth/userinfo.email']
    
    def __init__(self, *args, **kwargs):
        super(Google, self).__init__(*args, **kwargs)
        
        # Handle special Google requirements to be able to refresh the access token.
        if self.offline:
            if not 'access_type' in self.user_authorisation_params:
                # Google needs access_type=offline param in the user authorisation request.
                self.user_authorisation_params['access_type'] = 'offline'
            if not 'approval_prompt' in self.user_authorisation_params:
                # And also approval_prompt=force.
                self.user_authorisation_params['approval_prompt'] = 'force'
    
    
    @staticmethod
    def _x_user_parser(user, data):
        user.name = data.get('name')
        user.first_name = data.get('given_name')
        user.last_name = data.get('family_name')
        return user
    
    
    def _x_scope_parser(self, scope):
        """
        Google has space-separated scopes
        """
        return ' '.join(scope)
    

class Reddit(OAuth2):
    """
    Reddit |oauth2|_ provider.
    
    .. note::
        
        Currently credentials refreshment returns ``{"error": "invalid_request"}``.
    
    * Dashboard: https://ssl.reddit.com/prefs/apps
    * Docs: https://github.com/reddit/reddit/wiki/OAuth2
    * API reference: http://www.reddit.com/dev/api
    """
    
    user_authorisation_url = 'https://ssl.reddit.com/api/v1/authorize'
    access_token_url = 'https://ssl.reddit.com/api/v1/access_token'
    user_info_url = 'https://oauth.reddit.com/api/v1/me.json'
    
    user_info_scope = ['identity']
    
    def __init__(self, *args, **kwargs):
        super(Reddit, self).__init__(*args, **kwargs)
        
        if self.offline:
            if not 'duration' in self.user_authorisation_params:
                # http://www.reddit.com/r/changelog/comments/11jab9/reddit_change_permanent_oauth_grants_using/
                self.user_authorisation_params['duration'] = 'permanent'
    
    
    @classmethod
    def _x_credentials_parser(cls, credentials, data):
        if data.get('token_type') == 'bearer':
            credentials.token_type = cls.BEARER
        return credentials
    

class Viadeo(OAuth2):
    """
    Viadeo |oauth2|_ provider.
    
    * Dashboard: http://dev.viadeo.com/dashboard/
    * Docs: http://dev.viadeo.com/documentation/authentication/oauth-authentication/
    * API reference: http://dev.viadeo.com/documentation/
    
    .. note::
        
        Viadeo doesn't support **credentials refreshment**.
        As stated in their `docs <http://dev.viadeo.com/documentation/authentication/oauth-authentication/>`_:
            "The access token has an infinite time to live."
    
    """
    
    user_authorisation_url = 'https://secure.viadeo.com/oauth-provider/authorize2'
    access_token_url = 'https://secure.viadeo.com/oauth-provider/access_token2'
    user_info_url = 'https://api.viadeo.com/me'
    
    @classmethod
    def _x_credentials_parser(cls, credentials, data):
        if data.get('token_type') == 'bearer_token':
            credentials.token_type = cls.BEARER
        return credentials
    
    
    @staticmethod
    def _x_refresh_credentials_if(credentials):
        # Never refresh.
        return False
    
    
    @staticmethod
    def _x_user_parser(user, data):
        user.username = data.get('nickname')
        user.picture = data.get('picture_large')
        user.picture = data.get('picture_large')
        user.locale = data.get('language')
        user.email = data.get('')
        user.email = data.get('')
        user.country = data.get('location', {}).get('country')
        user.city = data.get('location', {}).get('city')
        user.postal_code = data.get('location', {}).get('zipcode')
        user.timezone = data.get('location', {}).get('timezone')
        
        return user


class WindowsLive(OAuth2):
    """
    Windows Live |oauth2|_ provider.
    
    * Dashboard: https://manage.dev.live.com/Applications/Index
    * Docs: http://msdn.microsoft.com/en-us/library/live/hh826528.aspx
    * API explorer: http://isdk.dev.live.com/?mkt=en-us
    """
    
    user_authorisation_url = 'https://oauth.live.com/authorize'
    access_token_url = 'https://oauth.live.com/token'
    user_info_url = 'https://apis.live.net/v5.0/me'
    
    user_info_scope = ['wl.basic', 'wl.emails', 'wl.photos']
    
    def __init__(self, *args, **kwargs):
        super(WindowsLive, self).__init__(*args, **kwargs)
        
        if self.offline:
            if not 'wl.offline_access' in self.scope:
                self.scope.append('wl.offline_access')
    
    
    @classmethod
    def _x_credentials_parser(cls, credentials, data):
        if data.get('token_type') == 'bearer':
            credentials.token_type = cls.BEARER
        return credentials
    
    
    @staticmethod
    def _x_user_parser(user, data):
        user.email = data.get('emails', {}).get('preferred')
        user.picture = 'https://apis.live.net/v5.0/{}/picture'.format(data.get('id'))
        return user














