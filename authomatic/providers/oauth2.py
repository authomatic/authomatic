# -*- coding: utf-8 -*-
"""
|oauth2| Providers
-------------------

Providers which implement the |oauth2|_ protocol.

.. autosummary::
    
    OAuth2
    Behance
    Bitly
    Cosm
    DeviantART
    Facebook
    Foursquare
    GitHub
    Google
    LinkedIn
    PayPal
    Reddit
    Viadeo
    VK
    WindowsLive
    Yammer
    Yandex
    
"""

from urllib import urlencode
import datetime
import logging

from authomatic import providers
from authomatic.exceptions import CancellationError, FailureError, OAuth2Error
import authomatic.core as core

__all__ = ['OAuth2', 'Behance', 'Bitly', 'Cosm', 'DeviantART', 'Facebook', 'Foursquare', 'GitHub',
           'Google', 'LinkedIn', 'PayPal', 'Reddit', 'Viadeo', 'VK', 'WindowsLive', 'Yammer', 'Yandex']


class OAuth2(providers.AuthorizationProvider):
    """
    Base class for |oauth2|_ providers.
    """
    
    PROVIDER_TYPE_ID = 2
    TOKEN_TYPES = ['', 'Bearer']
    
    #: A scope preset to get most of the **user** info.
    #: Use it in the :doc:`config` like ``{'scope': oauth2.Facebook.user_info_scope}``.
    user_info_scope = []
    
    #: :class:`bool` If ``False``, the provider doesn't support CSRF protection.
    supports_csrf_protection = True
    
    token_request_method = 'POST'  # method for requesting an access token
    
    def __init__(self, *args, **kwargs):
        """
        Accepts additional keyword arguments:
        
        :param list scope:
            List of strings specifying requested permissions as described in the
            `OAuth 2.0 spec <http://tools.ietf.org/html/rfc6749#section-3.3>`_.
        
        :param bool offline:
            If ``True`` the **provider** will be set up to request an *offline access token*.
            default is ``False``.
        
        As well as those inherited from :class:`.AuthorizationProvider` constructor.
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
    def create_request_elements(cls, request_type, credentials, url, method='GET', params=None,
                                headers=None, body='', secret=None, redirect_uri='', scope='', csrf=''):
        """
        Creates |oauth2| request elements.
        """
        
        headers = headers or {}
        params = params or {}
        
        consumer_key = credentials.consumer_key or ''
        consumer_secret = credentials.consumer_secret or ''
        token = credentials.token or ''
        refresh_token = credentials.refresh_token or credentials.token or ''
        
        # Separate url base and query parameters.
        url, base_params = cls._split_url(url)
                
        # Add params extracted from URL.
        params.update(dict(base_params))
        
        if request_type == cls.USER_AUTHORIZATION_REQUEST_TYPE:
            # User authorization request.
            # TODO: Raise error for specific message for each missing argument.
            if consumer_key and redirect_uri and (csrf or not cls.supports_csrf_protection):
                params['client_id'] = consumer_key
                params['redirect_uri'] = redirect_uri
                params['scope'] = scope
                params['state'] = csrf
                params['response_type'] = 'code'
                
                # Add authorization header
                headers.update(cls._authorization_header(credentials))
            else:
                raise OAuth2Error('Credentials with valid consumer_key and arguments redirect_uri, scope and ' + \
                                  'state are required to create OAuth 2.0 user authorization request elements!')
        
        elif request_type == cls.ACCESS_TOKEN_REQUEST_TYPE:
            # Access token request.
            if consumer_key and consumer_secret:
                params['code'] = token
                params['client_id'] = consumer_key
                params['client_secret'] = consumer_secret
                params['redirect_uri'] = redirect_uri
                params['grant_type'] = 'authorization_code'
                
                # TODO: Check whether all providers accept it
                headers.update(cls._authorization_header(credentials))
            else:
                raise OAuth2Error('Credentials with valid token, consumer_key, consumer_secret and argument ' + \
                                  'redirect_uri are required to create OAuth 2.0 access token request elements!')
        
        elif request_type == cls.REFRESH_TOKEN_REQUEST_TYPE:
            # Refresh access token request.
            if refresh_token and consumer_key and consumer_secret:
                params['refresh_token'] = refresh_token
                params['client_id'] = consumer_key
                params['client_secret'] = consumer_secret
                params['grant_type'] = 'refresh_token'
            else:
                raise OAuth2Error('Credentials with valid refresh_token, consumer_key, consumer_secret ' + \
                                  'are required to create OAuth 2.0 refresh token request elements!')
        
        elif request_type == cls.PROTECTED_RESOURCE_REQUEST_TYPE:
            # Protected resource request.
            
            # Add Authorization header. See: http://tools.ietf.org/html/rfc6749#section-7.1
            if credentials.token_type == cls.BEARER:
                # http://tools.ietf.org/html/rfc6750#section-2.1
                headers.update({'Authorization': 'Bearer {}'.format(credentials.token)})
                
            elif token:
                params['access_token'] = token
            else:
                raise OAuth2Error('Credentials with valid token are required to create ' + \
                                  'OAuth 2.0 protected resources request elements!')
        
        request_elements = core.RequestElements(url, method, params, headers, body)
        
        return cls._x_request_elements_filter(request_type, request_elements, credentials)
    
    
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
    def reconstruct(cls, deserialized_tuple, credentials, cfg):
        
        token, refresh_token, expiration_time, token_type = deserialized_tuple
        
        credentials.token = token
        credentials.refresh_token = refresh_token
        credentials.expiration_time = expiration_time
        credentials.token_type=cls.TOKEN_TYPES[int(token_type)]
        
        return credentials
    
    
    def refresh_credentials(self, credentials):
        """
        Refreshes :class:`.Credentials` if it gives sense.
        
        :param credentials:
            :class:`.Credentials` to be refreshed.
        
        :returns:
            :class:`.Response`.
        """
        
        if not self._x_refresh_credentials_if(credentials):
            return
        
        # We need consumer key and secret to make this kind of request.
        cfg = credentials.config.get(credentials.provider_name)
        credentials.consumer_key = cfg.get('consumer_key')
        credentials.consumer_secret = cfg.get('consumer_secret')
        
        request_elements = self.create_request_elements(request_type=self.REFRESH_TOKEN_REQUEST_TYPE,
                                                        credentials=credentials,
                                                        url=self.access_token_url,
                                                        method='POST')
        
        self._log(logging.INFO, 'Refreshing credentials.')
        response = self._fetch(*request_elements)
        
        # We no longer need consumer info.
        credentials.consumer_key = None
        credentials.consumer_secret = None
        
        # Extract the refreshed data.
        access_token = response.data.get('access_token')
        refresh_token = response.data.get('refresh_token')
        
        # Update credentials only if there is access token.
        if access_token:
            credentials.token = access_token
            credentials.expire_in = response.data.get('expires_in')
            
            # Update refresh token only if there is a new one.
            if refresh_token:
                credentials.refresh_token = refresh_token
            
            # Handle different naming conventions across providers.
            credentials = self._x_credentials_parser(credentials, response.data)
        
        return response
    
    
    @providers.login_decorator
    def login(self):
        
        # get request parameters from which we can determine the login phase
        authorization_code = self.params.get('code')
        error = self.params.get('error')
        error_message = self.params.get('error_message')
        state = self.params.get('state')      
        
        if authorization_code or not self.user_authorization_url:
            
            if authorization_code:
                #===================================================================
                # Phase 2 after redirect with success
                #===================================================================
                
                self._log(logging.INFO, 'Continuing OAuth 2.0 authorization procedure after redirect.')
                
                # validate CSRF token
                if self.supports_csrf_protection:
                    self._log(logging.INFO, 'Validating request by comparing request state with stored state.')
                    stored_state = self._session_get('state')
                    
                    if not stored_state:
                        raise FailureError('Unable to retrieve stored state!')
                    elif not stored_state == state:
                        raise FailureError('The returned state "{}" doesn\'t match with the stored state!'.format(state),
                                           url=self.user_authorization_url)
                    self._log(logging.INFO, 'Request is valid.')
                else:
                    self._log(logging.WARN, 'Skipping CSRF validation!')
            
            elif not self.user_authorization_url:
                #===================================================================
                # Phase 1 without user authorization redirect.
                #===================================================================
                
                self._log(logging.INFO, 'Starting OAuth 2.0 authorization procedure without ' + \
                                        'user authorization redirect.')
            
            # exchange authorization code for access token by the provider
            self._log(logging.INFO, 'Fetching access token from {}.'.format(self.access_token_url))
            
            self.credentials.token = authorization_code
            
            request_elements = self.create_request_elements(request_type=self.ACCESS_TOKEN_REQUEST_TYPE,
                                                             credentials=self.credentials,
                                                             url=self.access_token_url,
                                                             method=self.token_request_method,
                                                             redirect_uri=self.url,
                                                             params=self.access_token_params,
                                                             headers=self.access_token_headers)
            
            response = self._fetch(*request_elements)
            
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
            
            # OAuth 2.0 credentials need access_token, refresh_token, token_type and expire_in.
            self.credentials.token = access_token
            self.credentials.refresh_token = refresh_token
            self.credentials.expire_in = response.data.get('expires_in')
            self.credentials.token_type = response.data.get('token_type', '')
            # sWe don't need these two guys anymore.
            self.credentials.consumer_key = ''
            self.credentials.consumer_secret = ''
            
            # update credentials
            self.credentials = self._x_credentials_parser(self.credentials, response.data)            
            
            # create user
            self._update_or_create_user(response.data, self.credentials)
            
            #===================================================================
            # We're done!
            #===================================================================
            
        elif error or error_message:
            #===================================================================
            # Phase 2 after redirect with error
            #===================================================================
            
            error_reason = self.params.get('error_reason')
            error_description = self.params.get('error_description') or error_message
            
            if error_reason == 'user_denied':
                raise CancellationError(error_description, url=self.user_authorization_url)
            else:
                raise FailureError(error_description, url=self.user_authorization_url)
            
        elif not self.params:
            #===================================================================
            # Phase 1 before redirect
            #===================================================================
            
            self._log(logging.INFO, 'Starting OAuth 2.0 authorization procedure.')
            
            csrf = ''
            if self.supports_csrf_protection:
                # generate csfr
                csrf = self.csrf_generator(self.settings.secret)
                # and store it to session
                self._session_set('state', csrf)
            else:
                self._log(logging.WARN, 'Provider doesn\'t support CSRF validation!')
                        
            request_elements = self.create_request_elements(request_type=self.USER_AUTHORIZATION_REQUEST_TYPE,
                                                            credentials=self.credentials,
                                                            url=self.user_authorization_url,
                                                            redirect_uri=self.url,
                                                            scope=self._x_scope_parser(self.scope),
                                                            csrf=csrf,
                                                            params=self.user_authorization_params)
            
            self._log(logging.INFO, 'Redirecting user to {}.'.format(request_elements.full_url))
            
            self.redirect(request_elements.full_url)


class Behance(OAuth2):
    """
    Behance |oauth2| provider.
    
    * Dashboard: http://www.behance.net/dev/apps
    * Docs: http://www.behance.net/dev/authentication
    * API reference: http://www.behance.net/dev/api/endpoints/
    """
    
    user_authorization_url = 'https://www.behance.net/v2/oauth/authenticate'
    access_token_url = 'https://www.behance.net/v2/oauth/token'
    user_info_url = ''
    
    user_info_scope = ['activity_read']
    
    def _x_scope_parser(self, scope):
        """
        Behance has pipe-separated scopes
        """
        return '|'.join(scope)
    
    @staticmethod
    def _x_user_parser(user, data):
        
        _user = data.get('user', {})
        
        user.id = _user.get('id')
        user.first_name = _user.get('first_name')
        user.last_name = _user.get('last_name')
        user.username = _user.get('username')
        user.city = _user.get('city')
        user.country = _user.get('country')
        user.link = _user.get('url')
        user.name = _user.get('display_name')
        user.picture = _user.get('images', {}).get('138')
        
        return user


class Bitly(OAuth2):
    """
    Bitly |oauth2| provider.
    
    .. warning::
        
        |no-csrf|
    
    * Dashboard: https://bitly.com/a/oauth_apps
    * Docs: http://dev.bitly.com/authentication.html
    * API reference: http://dev.bitly.com/api.html

    Supported :class:`.User` properties:

    * id
    * link
    * name
    * picture
    * username

    Unsupported :class:`.User` properties:

    * birth_date
    * city
    * country
    * email
    * first_name
    * gender
    * last_name
    * locale
    * nickname
    * phone
    * postal_code
    * timezone

    """

    supported_user_attributes = core.SupportedUserAttributes(
        id=True,
        link=True,
        name=True,
        picture=True,
        username=True
    )
    
    supports_csrf_protection = False
    _x_use_authorization_header = False
    
    user_authorization_url = 'https://bitly.com/oauth/authorize'
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
    Cosm |oauth2| provider.
    
    .. note::
        
        Cosm doesn't provide any *user info URL*.
    
    * Dashboard: https://cosm.com/users/{your_username}/apps
    * Docs: https://cosm.com/docs/
    * API reference: https://cosm.com/docs/v2/
    """
    
    user_authorization_url = 'https://cosm.com/oauth/authenticate'
    access_token_url = 'https://cosm.com/oauth/token'
    user_info_url = ''
    
    @staticmethod
    def _x_user_parser(user, data):
        user.id = user.username = data.get('user')
        return user


class DeviantART(OAuth2):
    """
    DeviantART |oauth2| provider.
    
    * Dashboard: https://www.deviantart.com/settings/myapps
    * Docs: https://www.deviantart.com/developers/authentication
    * API reference: http://www.deviantart.com/developers/oauth2

    Supported :class:`.User` properties:

    * name
    * picture
    * username

    Unsupported :class:`.User` properties:

    * birth_date
    * city
    * country
    * email
    * first_name
    * gender
    * id
    * last_name
    * link
    * locale
    * nickname
    * phone
    * postal_code
    * timezone

    """
    
    user_authorization_url = 'https://www.deviantart.com/oauth2/draft15/authorize'
    access_token_url = 'https://www.deviantart.com/oauth2/draft15/token'
    user_info_url = 'https://www.deviantart.com/api/oauth2/user/whoami'

    user_info_scope = ['basic']

    supported_user_attributes = core.SupportedUserAttributes(
        name=True,
        picture=True,
        username=True
    )
    
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
    Facebook |oauth2| provider.
    
    * Dashboard: https://developers.facebook.com/apps
    * Docs: http://developers.facebook.com/docs/howtos/login/server-side-login/
    * API reference: http://developers.facebook.com/docs/reference/api/
    * API explorer: http://developers.facebook.com/tools/explorer

    Supported :class:`.User` properties:

    * city
    * country
    * email
    * first_name
    * gender
    * id
    * last_name
    * link
    * locale
    * name
    * picture
    * timezone
    * username

    Unsupported :class:`.User` properties:

    * birth_date
    * nickname
    * phone
    * postal_code

    """
    
    user_authorization_url = 'https://www.facebook.com/dialog/oauth'
    access_token_url = 'https://graph.facebook.com/oauth/access_token'
    user_info_url = 'https://graph.facebook.com/me'
    user_info_scope = ['user_about_me', 'email']
    same_origin = False

    supported_user_attributes = core.SupportedUserAttributes(
        id=True,
        email=True,
        username=True,
        name=True,
        first_name=True,
        last_name=True,
        city=True,
        country=True,
        gender=True,
        link=True,
        locale=True,
        picture=True,
        timezone=True
    )
    
    @classmethod
    def _x_request_elements_filter(cls, request_type, request_elements, credentials):
        
        if request_type == cls.REFRESH_TOKEN_REQUEST_TYPE:
            # As always, Facebook has it's original name for "refresh_token"!
            url, method, params, headers, body = request_elements
            params['fb_exchange_token'] = params.pop('refresh_token')
            params['grant_type'] = 'fb_exchange_token'
            request_elements = core.RequestElements(url, method, params, headers, body)
        
        return request_elements
    
    
    def __init__(self, *args, **kwargs):
        super(Facebook, self).__init__(*args, **kwargs)
        
        # Handle special Facebook requirements to be able to refresh the access token.
        if self.offline:
            # Facebook needs an offline_access scope.
            if not 'offline_access' in self.scope:
                self.scope.append('offline_access')
        
        if self.popup:
            self.user_authorization_url += '?display=popup'
    
    
    @staticmethod
    def _x_user_parser(user, data):
        user.picture = 'http://graph.facebook.com/{}/picture?type=large'.format(data.get('username'))

        location = data.get('location', {}).get('name')
        if location and location.split:
            split_location = location.split(', ')
            user.city = split_location[0].strip()
            if len(split_location) > 1:
                user.country = split_location[1].strip()

        return user
    
    
    @staticmethod
    def _x_credentials_parser(credentials, data):
        """
        We need to override this method to fix Facebooks naming deviation.
        """
        
        # Facebook returns "expires" instead of "expires_in".
        credentials.expire_in = data.get('expires')
        
        return credentials
    
    
    @staticmethod
    def _x_refresh_credentials_if(credentials):
        # Always refresh.
        return True


class Foursquare(OAuth2):
    """
    Foursquare |oauth2| provider.
    
    * Dashboard: https://foursquare.com/developers/apps
    * Docs: https://developer.foursquare.com/overview/auth.html
    * API reference: https://developer.foursquare.com/docs/
    """
    
    user_authorization_url = 'https://foursquare.com/oauth2/authenticate'
    access_token_url = 'https://foursquare.com/oauth2/access_token'
    user_info_url = 'https://api.foursquare.com/v2/users/self'
    
    same_origin = False
    
    
    @classmethod
    def _x_request_elements_filter(cls, request_type, request_elements, credentials):
        
        if request_type == cls.PROTECTED_RESOURCE_REQUEST_TYPE:
            # Foursquare uses OAuth 1.0 "oauth_token" for what should be "access_token" in OAuth 2.0!
            url, method, params, headers, body = request_elements
            params['oauth_token'] = params.pop('access_token')
            request_elements = core.RequestElements(url, method, params, headers, body)
        
        return request_elements
    
    
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
    GitHub |oauth2| provider.
    
    * Dashboard: https://github.com/settings/applications/
    * Docs: http://developer.github.com/v3/#authentication
    * API reference: http://developer.github.com/v3/
    
    .. note::
        
        GitHub API `documentation <http://developer.github.com/v3/#user-agent-required>`_ sais:
        
            all API requests MUST include a valid ``User-Agent`` header.
        
        You can apply a default ``User-Agent`` header for all API calls in the config like this:
        
        .. code-block:: python
            :emphasize-lines: 6
        
            CONFIG = {
                'github': {
                    'class_': oauth2.GitHub,
                    'consumer_key': '#####',
                    'consumer_secret': '#####',
                    'access_headers': {'User-Agent': 'Awesome-Octocat-App'},
                }
            }
    
    """
    
    user_authorization_url = 'https://github.com/login/oauth/authorize'
    access_token_url = 'https://github.com/login/oauth/access_token'
    user_info_url = 'https://api.github.com/user'
    
    same_origin = False
    
    @staticmethod
    def _x_user_parser(user, data):
        user.username = data.get('login')
        user.picture = data.get('avatar_url')
        user.link = data.get('html_url')

        location = data.get('location', '')
        if location:
            split_location = location.split(',')
            user.city = split_location[0].strip()
            if len(split_location) > 1:
                user.country = split_location[1].strip()
            
        return user
    
    @classmethod
    def _x_credentials_parser(cls, credentials, data):
        if data.get('token_type') == 'bearer':
            credentials.token_type = cls.BEARER
        return credentials


class Google(OAuth2):
    """
    Google |oauth2| provider.
    
    * Dashboard: https://code.google.com/apis/console/
    * Docs: https://developers.google.com/accounts/docs/OAuth2
    * API reference: https://developers.google.com/gdata/docs/directory
    * API explorer: https://developers.google.com/oauthplayground/
    """
    
    user_authorization_url = 'https://accounts.google.com/o/oauth2/auth'
    access_token_url = 'https://accounts.google.com/o/oauth2/token'
    user_info_url = 'https://www.googleapis.com/plus/v1/people/me'
    
    user_info_scope = ['profile',
                       'email']
    
    def __init__(self, *args, **kwargs):
        super(Google, self).__init__(*args, **kwargs)
        
        # Handle special Google requirements to be able to refresh the access token.
        if self.offline:
            if not 'access_type' in self.user_authorization_params:
                # Google needs access_type=offline param in the user authorization request.
                self.user_authorization_params['access_type'] = 'offline'
            if not 'approval_prompt' in self.user_authorization_params:
                # And also approval_prompt=force.
                self.user_authorization_params['approval_prompt'] = 'force'
    
    
    @staticmethod
    def _x_user_parser(user, data):

        user.id = data.get('sub') or data.get('id')
        user.name = data.get('displayName')
        user.first_name = data.get('name',{}).get('given_name')
        user.last_name = data.get('name',{}).get('family_name')
        user.link = data.get('url')
        user.picture = data.get('image',{}).get('url')
        try:
            user.birth_date = datetime.datetime.strptime(data.get('birthdate'), "%Y-%m-%d")
        except:
            user.birth_date = data.get('birthdate')
        return user
    
    
    def _x_scope_parser(self, scope):
        """
        Google has space-separated scopes
        """
        return ' '.join(scope)


class LinkedIn(OAuth2):
    """
    Linked In |oauth2| provider.
    
    .. note::
        
        Doesn't support access token refreshment.
    
    * Dashboard: https://www.linkedin.com/secure/developer
    * Docs: http://developer.linkedin.com/documents/authentication
    * API reference: http://developer.linkedin.com/rest
    """
    
    user_authorization_url = 'https://www.linkedin.com/uas/oauth2/authorization'
    access_token_url = 'https://www.linkedin.com/uas/oauth2/accessToken'
    user_info_url = 'https://api.linkedin.com/v1/people/~:' + \
                    '(id,first-name,last-name,formatted-name,location,picture-url,public-profile-url,email-address,date-of-birth,phone-numbers)?format=json'
    
    user_info_scope = ['r_fullprofile', 'r_emailaddress', 'r_contactinfo']
    
    token_request_method = 'GET'  # To avoid a bug with OAuth2.0 on Linkedin
    # http://developer.linkedin.com/forum/unauthorized-invalid-or-expired-token-immediately-after-receiving-oauth2-token
    
    @classmethod
    def _x_request_elements_filter(cls, request_type, request_elements, credentials):
        
        if request_type == cls.PROTECTED_RESOURCE_REQUEST_TYPE:
            # LinkedIn too has it's own terminology!
            url, method, params, headers, body = request_elements
            params['oauth2_access_token'] = params.pop('access_token')
            request_elements = core.RequestElements(url, method, params, headers, body)
        
        return request_elements
    
    
    @staticmethod
    def _x_user_parser(user, data):
        
        user.first_name = data.get('firstName')
        user.last_name = data.get('lastName')
        user.email = data.get('emailAddress')
        user.name = data.get('formattedName')
        user.country = data.get('location', {}).get('name')
        user.phone = data.get('phoneNumbers', {}).get('values', [{}])[0].get('phoneNumber')
        user.picture = data.get('pictureUrl')
        user.link = data.get('publicProfileUrl')
        
        return user


class PayPal(OAuth2):
    """
    PayPal |oauth2| provider.
    
    .. warning::
        
        Paypal doesn't redirect the **user** to authorize your app!
        It grants you an **access token** based on your **app's** key and secret instead.
    
    * Dashboard: https://developer.paypal.com/webapps/developer/applications
    * Docs: https://developer.paypal.com/webapps/developer/docs/integration/direct/make-your-first-call/
    * API reference: https://developer.paypal.com/webapps/developer/docs/api/
    """
    
    _x_use_authorization_header = True
    
    @classmethod
    def _x_request_elements_filter(cls, request_type, request_elements, credentials):
        
        if request_type == cls.ACCESS_TOKEN_REQUEST_TYPE:
            url, method, params, headers, body = request_elements
            params['grant_type'] = 'client_credentials'
            request_elements = core.RequestElements(url, method, params, headers, body)
        
        return request_elements
    
    
    user_authorization_url = ''
    access_token_url = 'https://api.sandbox.paypal.com/v1/oauth2/token'
    user_info_url = ''


class Reddit(OAuth2):
    """
    Reddit |oauth2| provider.
    
    .. note::
        
        Currently credentials refreshment returns ``{"error": "invalid_request"}``.
    
    * Dashboard: https://ssl.reddit.com/prefs/apps
    * Docs: https://github.com/reddit/reddit/wiki/OAuth2
    * API reference: http://www.reddit.com/dev/api
    """
    
    user_authorization_url = 'https://ssl.reddit.com/api/v1/authorize'
    access_token_url = 'https://ssl.reddit.com/api/v1/access_token'
    user_info_url = 'https://oauth.reddit.com/api/v1/me.json'
    
    user_info_scope = ['identity']
    
    def __init__(self, *args, **kwargs):
        super(Reddit, self).__init__(*args, **kwargs)
        
        if self.offline:
            if not 'duration' in self.user_authorization_params:
                # http://www.reddit.com/r/changelog/comments/11jab9/reddit_change_permanent_oauth_grants_using/
                self.user_authorization_params['duration'] = 'permanent'
    
    
    @classmethod
    def _x_credentials_parser(cls, credentials, data):
        if data.get('token_type') == 'bearer':
            credentials.token_type = cls.BEARER
        return credentials


class Viadeo(OAuth2):
    """
    Viadeo |oauth2| provider.
    
    * Dashboard: http://dev.viadeo.com/dashboard/
    * Docs: http://dev.viadeo.com/documentation/authentication/oauth-authentication/
    * API reference: http://dev.viadeo.com/documentation/
    
    .. note::
        
        Viadeo doesn't support **credentials refreshment**.
        As stated in their `docs <http://dev.viadeo.com/documentation/authentication/oauth-authentication/>`_:
        "The access token has an infinite time to live."
    
    """
    
    user_authorization_url = 'https://secure.viadeo.com/oauth-provider/authorize2'
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


class VK(OAuth2):
    """
    VK.com |oauth2| provider.
    
    * Dashboard: Could not find any. You must do it like this: http://vk.com/editapp?id={consumer_key}
    * Docs: http://vk.com/developers.php?oid=-17680044&p=Authorizing_Sites
    * API reference: http://vk.com/developers.php?oid=-17680044&p=API_Method_Description
    
    .. note::
        
        VK uses a `bitmask scope <http://vk.com/developers.php?oid=-17680044&p=Application_Rights>`_!
        Use it like this:
        
    .. code-block:: python
        :emphasize-lines: 7
        
        CONFIG = {
            'vk': {
                'class_': oauth2.VK,
                'consumer_key': '#####',
                'consumer_secret': '#####',
                'id': authomatic.provider_id(),
                'scope': ['1024'] # Always a single item.
            }
        }
    
    """
    
    user_authorization_url = 'http://api.vkontakte.ru/oauth/authorize'
    access_token_url = 'https://api.vkontakte.ru/oauth/access_token'
    user_info_url = 'https://api.vk.com/method/getProfiles?' + \
                    'fields=uid,first_name,last_name,nickname,sex,bdate,city,country,timezone,photo_big'
    
    
    def __init__(self, *args, **kwargs):
        super(VK, self).__init__(*args, **kwargs)
        
        if self.offline:
            if not 'offline' in self.scope:
                self.scope.append('offline')
    
    
    @staticmethod
    def _x_user_parser(user, data):
        _resp = data.get('response', [{}])[0]
        
        user.id = _resp.get('uid')
        user.first_name = _resp.get('first_name')
        user.last_name = _resp.get('last_name')
        user.nickname = _resp.get('nickname')
        user.city = _resp.get('city')
        user.country = _resp.get('country')
        user.timezone = _resp.get('timezone')
        user.picture = _resp.get('photo_big')
        
        return user


class WindowsLive(OAuth2):
    """
    Windows Live |oauth2| provider.
    
    * Dashboard: https://manage.dev.live.com/Applications/Index
    * Docs: http://msdn.microsoft.com/en-us/library/live/hh826528.aspx
    * API explorer: http://isdk.dev.live.com/?mkt=en-us
    """
    
    user_authorization_url = 'https://oauth.live.com/authorize'
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


class Yammer(OAuth2):
    """
    Yammer |oauth2| provider.
    
    .. warning::
        
        |no-csrf|
    
    * Dashboard: https://www.yammer.com/client_applications
    * Docs: https://developer.yammer.com/authentication/
    * API reference: https://developer.yammer.com/restapi/
    """
    
    user_authorization_url = 'https://www.yammer.com/dialog/oauth'
    access_token_url = 'https://www.yammer.com/oauth2/access_token.json'
    user_info_url = 'https://www.yammer.com/api/v1/users/current.json'
    
    supports_csrf_protection = False
    
    @classmethod
    def _x_credentials_parser(cls, credentials, data):
        
        _access_token = data.get('access_token', {})
        credentials.token = _access_token.get('token')
        _expire_in = _access_token.get('expires_at', 0)
        if _expire_in:
            credentials.expire_in = _expire_in
        
        return credentials
    
    @staticmethod
    def _x_user_parser(user, data):
        
        user.username = data.get('name')
        user.name = data.get('full_name')
        user.link = data.get('web_url')
        user.picture = data.get('mugshot_url')
        
        user.city, user.country = data.get('location', ',').split(',')
        user.city = user.city.strip()
        user.country = user.country.strip()
        
        # Contact
        _contact = data.get('contact', {})
        user.phone = _contact.get('phone_numbers', [{}])[0].get('number')
        _emails = _contact.get('email_addresses', [])
        for email in _emails:
            if email.get('type', '') == 'primary':
                user.email = email.get('address')
                break
        
        try:
            user.birth_date = datetime.datetime.strptime(data.get('birth_date'), "%B %d")
        except:
            user.birth_date = data.get('birth_date')
        
        return user


class Yandex(OAuth2):
    """
    Yandex |oauth2| provider.
    
    * Dashboard: https://oauth.yandex.com/client/my
    * Docs: http://api.yandex.com/oauth/doc/dg/reference/obtain-access-token.xml
    * API reference: 
    """
    
    user_authorization_url = 'https://oauth.yandex.com/authorize'
    access_token_url = 'https://oauth.yandex.com/token'
    user_info_url = 'https://login.yandex.ru/info'
    
    @classmethod
    def _x_credentials_parser(cls, credentials, data):
        if data.get('token_type') == 'bearer':
            credentials.token_type = cls.BEARER
        return credentials
    
    
    @staticmethod
    def _x_user_parser(user, data):
        
        # http://api.yandex.ru/login/doc/dg/reference/response.xml
        user.name = data.get('real_name')
        user.nickname = data.get('display_name')
        user.gender = data.get('Sex')
        user.email = data.get('Default_email')
        
        try:
            user.birth_date = datetime.datetime.strptime(data.get('birthday'), "%Y-%m-%d")
        except:
            user.birth_date = data.get('birthday')
        
        return user


# The provider type ID is generated from this list's indexes!
# Always append new providers at the end so that ids of existing providers don't change!
PROVIDER_ID_MAP = [OAuth2, Behance, Bitly, Cosm, DeviantART, Facebook, Foursquare, GitHub, Google, LinkedIn,
          PayPal, Reddit, Viadeo, VK, WindowsLive, Yammer, Yandex]









