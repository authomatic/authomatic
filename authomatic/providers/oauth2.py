# -*- coding: utf-8 -*-
"""
|oauth2| Providers
-------------------

Providers which implement the |oauth2|_ protocol.

.. autosummary::

    OAuth2
    Amazon
    Behance
    Bitly
    Cosm
    DeviantART
    Eventbrite
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

import base64
import datetime
import json
import logging

from authomatic.six.moves.urllib.parse import unquote
from authomatic import providers
from authomatic.exceptions import CancellationError, FailureError, OAuth2Error
import authomatic.core as core


__all__ = ['OAuth2', 'Amazon', 'Behance', 'Bitly', 'Cosm', 'DeviantART',
           'Eventbrite', 'Facebook', 'Foursquare', 'GitHub', 'Google',
           'LinkedIn', 'PayPal', 'Reddit', 'Viadeo', 'VK', 'WindowsLive',
           'Yammer', 'Yandex']


class OAuth2(providers.AuthorizationProvider):
    """
    Base class for |oauth2|_ providers.
    """

    PROVIDER_TYPE_ID = 2
    TOKEN_TYPES = ['', 'Bearer']

    #: A scope preset to get most of the **user** info.
    #: Use it in the :doc:`config` like
    #: ``{'scope': oauth2.Facebook.user_info_scope}``.
    user_info_scope = []

    #: :class:`bool` If ``False``, the provider doesn't support CSRF
    #: protection.
    supports_csrf_protection = True

    #: :class:`bool` If ``False``, the provider doesn't support user_state.
    supports_user_state = True

    token_request_method = 'POST'  # method for requesting an access token

    def __init__(self, *args, **kwargs):
        """
        Accepts additional keyword arguments:

        :param list scope:
            List of strings specifying requested permissions as described
            in the
            `OAuth 2.0 spec <http://tools.ietf.org/html/rfc6749#section-3.3>`_.

        :param bool offline:
            If ``True`` the **provider** will be set up to request an
            *offline access token*.
            Default is ``False``.

        As well as those inherited from :class:`.AuthorizationProvider`
        constructor.

        """

        super(OAuth2, self).__init__(*args, **kwargs)

        self.scope = self._kwarg(kwargs, 'scope', [])
        self.offline = self._kwarg(kwargs, 'offline', False)

    # ========================================================================
    # Internal methods
    # ========================================================================

    def _x_scope_parser(self, scope):
        """
        Override this to handle differences between accepted format of scope
        across providers.

        :attr list scope:
            List of scopes.

        """

        # pylint:disable=no-self-use

        # Most providers accept csv scope.
        return ','.join(scope) if scope else ''

    @classmethod
    def create_request_elements(
            cls, request_type, credentials, url, method='GET', params=None,
            headers=None, body='', secret=None, redirect_uri='', scope='',
            csrf='', user_state=''
    ):
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
            if consumer_key and redirect_uri and (
                    csrf or not cls.supports_csrf_protection):
                params['client_id'] = consumer_key
                params['redirect_uri'] = redirect_uri
                params['scope'] = scope
                if cls.supports_user_state:
                    params['state'] = base64.urlsafe_b64encode(
                        json.dumps(
                            {"csrf": csrf, "user_state": user_state}
                        ).encode('utf-8')
                    )
                else:
                    params['state'] = csrf
                params['response_type'] = 'code'

                # Add authorization header
                headers.update(cls._authorization_header(credentials))
            else:
                raise OAuth2Error(
                    'Credentials with valid consumer_key and arguments '
                    'redirect_uri, scope and state are required to create '
                    'OAuth 2.0 user authorization request elements!')

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
                raise OAuth2Error(
                    'Credentials with valid token, consumer_key, '
                    'consumer_secret and argument redirect_uri are required '
                    'to create OAuth 2.0 access token request elements!')

        elif request_type == cls.REFRESH_TOKEN_REQUEST_TYPE:
            # Refresh access token request.
            if refresh_token and consumer_key and consumer_secret:
                params['refresh_token'] = refresh_token
                params['client_id'] = consumer_key
                params['client_secret'] = consumer_secret
                params['grant_type'] = 'refresh_token'
            else:
                raise OAuth2Error(
                    'Credentials with valid refresh_token, consumer_key, '
                    'consumer_secret are required to create OAuth 2.0 '
                    'refresh token request elements!')

        elif request_type == cls.PROTECTED_RESOURCE_REQUEST_TYPE:
            # Protected resource request.

            # Add Authorization header. See:
            # http://tools.ietf.org/html/rfc6749#section-7.1
            if credentials.token_type == cls.BEARER:
                # http://tools.ietf.org/html/rfc6750#section-2.1
                headers.update(
                    {'Authorization': 'Bearer {0}'.format(credentials.token)})

            elif token:
                params['access_token'] = token
            else:
                raise OAuth2Error(
                    'Credentials with valid token are required to create '
                    'OAuth 2.0 protected resources request elements!')

        request_elements = core.RequestElements(
            url, method, params, headers, body)

        return cls._x_request_elements_filter(
            request_type, request_elements, credentials)

    @staticmethod
    def _x_refresh_credentials_if(credentials):
        """
        Override this to specify conditions when it gives sense to refresh
        credentials.

        .. warning::

            |classmethod|

        :param credentials:
            :class:`.Credentials`

        :returns:
            ``True`` or ``False``

        """

        if credentials.refresh_token:
            return True

    # ========================================================================
    # Exposed methods
    # ========================================================================

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
        credentials.token_type = cls.TOKEN_TYPES[int(token_type)]

        return credentials

    @classmethod
    def decode_state(cls, state, param='user_state'):
        """
        Decode state and return param.

        :param str state:
            state parameter passed through by provider

        :param str param:
            key to query from decoded state variable. Options include 'csrf'
            and 'user_state'.

        :returns:
            string value from decoded state

        """
        if state and cls.supports_user_state:
            # urlsafe_b64 may include = which the browser quotes so must
            # unquote Cast to str to void b64decode translation error. Base64
            # should be str compatible.
            return json.loads(base64.urlsafe_b64decode(
                unquote(str(state))).decode('utf-8'))[param]
        else:
            return state if param == 'csrf' else ''

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

        request_elements = self.create_request_elements(
            request_type=self.REFRESH_TOKEN_REQUEST_TYPE,
            credentials=credentials,
            url=self.access_token_url,
            method='POST'
        )

        self._log(logging.INFO, u'Refreshing credentials.')
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
            credentials = self._x_credentials_parser(
                credentials, response.data)

        return response

    @providers.login_decorator
    def login(self):

        # get request parameters from which we can determine the login phase
        authorization_code = self.params.get('code')
        error = self.params.get('error')
        error_message = self.params.get('error_message')
        state = self.params.get('state')
        # optional user_state to be passed in oauth2 state
        user_state = self.params.get('user_state', '')

        if authorization_code or not self.user_authorization_url:

            if authorization_code:
                # =============================================================
                # Phase 2 after redirect with success
                # =============================================================

                self._log(
                    logging.INFO,
                    u'Continuing OAuth 2.0 authorization procedure after '
                    u'redirect.')

                # validate CSRF token
                if self.supports_csrf_protection:
                    self._log(
                        logging.INFO,
                        u'Validating request by comparing request state with '
                        u'stored state.')
                    stored_csrf = self._session_get('csrf')

                    state_csrf = self.decode_state(state, 'csrf')
                    if not stored_csrf:
                        raise FailureError(u'Unable to retrieve stored state!')
                    elif stored_csrf != state_csrf:
                        raise FailureError(
                            u'The returned state csrf cookie "{0}" doesn\'t '
                            u'match with the stored state!'.format(
                                state_csrf
                            ),
                            url=self.user_authorization_url)
                    self._log(logging.INFO, u'Request is valid.')
                else:
                    self._log(logging.WARN, u'Skipping CSRF validation!')

            elif not self.user_authorization_url:
                # =============================================================
                # Phase 1 without user authorization redirect.
                # =============================================================

                self._log(
                    logging.INFO,
                    u'Starting OAuth 2.0 authorization procedure without '
                    u'user authorization redirect.')

            # exchange authorization code for access token by the provider
            self._log(
                logging.INFO,
                u'Fetching access token from {0}.'.format(
                    self.access_token_url))

            self.credentials.token = authorization_code

            request_elements = self.create_request_elements(
                request_type=self.ACCESS_TOKEN_REQUEST_TYPE,
                credentials=self.credentials,
                url=self.access_token_url,
                method=self.token_request_method,
                redirect_uri=self.url,
                params=self.access_token_params,
                headers=self.access_token_headers
            )

            response = self._fetch(*request_elements)
            self.access_token_response = response

            access_token = response.data.get('access_token', '')
            refresh_token = response.data.get('refresh_token', '')

            if response.status != 200 or not access_token:
                raise FailureError(
                    'Failed to obtain OAuth 2.0 access token from {0}! '
                    'HTTP status: {1}, message: {2}.'.format(
                        self.access_token_url,
                        response.status,
                        response.content
                    ),
                    original_message=response.content,
                    status=response.status,
                    url=self.access_token_url)

            self._log(logging.INFO, u'Got access token.')

            if refresh_token:
                self._log(logging.INFO, u'Got refresh access token.')

            # OAuth 2.0 credentials need access_token, refresh_token,
            # token_type and expire_in.
            self.credentials.token = access_token
            self.credentials.refresh_token = refresh_token
            self.credentials.expire_in = response.data.get('expires_in')
            self.credentials.token_type = response.data.get('token_type', '')
            # sWe don't need these two guys anymore.
            self.credentials.consumer_key = ''
            self.credentials.consumer_secret = ''

            # update credentials
            self.credentials = self._x_credentials_parser(
                self.credentials, response.data)

            # create user
            self._update_or_create_user(response.data, self.credentials)

            # =================================================================
            # We're done!
            # =================================================================

        elif error or error_message:
            # =================================================================
            # Phase 2 after redirect with error
            # =================================================================

            error_reason = self.params.get('error_reason') or error
            error_description = self.params.get('error_description') \
                or error_message or error

            if error_reason and 'denied' in error_reason:
                raise CancellationError(error_description,
                                        url=self.user_authorization_url)
            else:
                raise FailureError(
                    error_description,
                    url=self.user_authorization_url)

        elif (
                not self.params
                or len(self.params) == 1
                and 'user_state' in self.params
        ):
            # =================================================================
            # Phase 1 before redirect
            # =================================================================

            self._log(
                logging.INFO,
                u'Starting OAuth 2.0 authorization procedure.')

            csrf = ''
            if self.supports_csrf_protection:
                # generate csfr
                csrf = self.csrf_generator(self.settings.secret)
                # and store it to session
                self._session_set('csrf', csrf)
            else:
                self._log(
                    logging.WARN,
                    u'Provider doesn\'t support CSRF validation!')

            request_elements = self.create_request_elements(
                request_type=self.USER_AUTHORIZATION_REQUEST_TYPE,
                credentials=self.credentials,
                url=self.user_authorization_url,
                redirect_uri=self.url,
                scope=self._x_scope_parser(
                    self.scope),
                csrf=csrf,
                user_state=user_state,
                params=self.user_authorization_params
            )

            self._log(
                logging.INFO,
                u'Redirecting user to {0}.'.format(
                    request_elements.full_url))

            self.redirect(request_elements.full_url)


class Amazon(OAuth2):
    """
    Amazon |oauth2| provider.

    Thanks to `Ghufran Syed <https://github.com/ghufransyed>`__.

    * Dashboard: https://developer.amazon.com/lwa/sp/overview.html
    * Docs: https://developer.amazon.com/public/apis/engage/login-with-amazon/docs/conceptual_overview.html
    * API reference: https://developer.amazon.com/public/apis

    .. note::

        Amazon only accepts **redirect_uri** with **https** schema,
        Therefore the *login handler* must also be accessible through
        **https**.

    Supported :class:`.User` properties:

    * email
    * id
    * name
    * postal_code

    Unsupported :class:`.User` properties:

    * birth_date
    * city
    * country
    * first_name
    * gender
    * last_name
    * link
    * locale
    * nickname
    * phone
    * picture
    * timezone
    * username

    """

    user_authorization_url = 'https://www.amazon.com/ap/oa'
    access_token_url = 'https://api.amazon.com/auth/o2/token'
    user_info_url = 'https://api.amazon.com/user/profile'
    user_info_scope = ['profile', 'postal_code']

    supported_user_attributes = core.SupportedUserAttributes(
        email=True,
        id=True,
        name=True,
        postal_code=True
    )

    def _x_scope_parser(self, scope):
        # Amazon has space-separated scopes
        return ' '.join(scope)

    @staticmethod
    def _x_user_parser(user, data):
        user.id = data.get('user_id')
        return user

    @classmethod
    def _x_credentials_parser(cls, credentials, data):
        if data.get('token_type') == 'bearer':
            credentials.token_type = cls.BEARER
        return credentials


class Behance(OAuth2):
    """
    Behance |oauth2| provider.

    .. note::

        Behance doesn't support third party authorization anymore,
        which renders this class pretty much useless.

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
        Behance has pipe-separated scopes.
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
            if 'grant_type' not in self.access_token_params:
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

    .. note::

        Although it is not documented anywhere, DeviantART requires the
        *access token* request to contain a ``User-Agent`` header.
        You can apply a default ``User-Agent`` header for all API calls in the
        config like this:

        .. code-block:: python
            :emphasize-lines: 6

            CONFIG = {
                'deviantart': {
                    'class_': oauth2.DeviantART,
                    'consumer_key': '#####',
                    'consumer_secret': '#####',
                    'access_headers': {'User-Agent': 'Some User Agent'},
                }
            }

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

    user_authorization_url = 'https://www.deviantart.com/oauth2/authorize'
    access_token_url = 'https://www.deviantart.com/oauth2/token'
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
            if 'grant_type' not in self.access_token_params:
                self.access_token_params['grant_type'] = 'refresh_token'

    @staticmethod
    def _x_user_parser(user, data):
        user.picture = data.get('usericonurl')
        return user


class Eventbrite(OAuth2):
    """
    Eventbrite |oauth2| provider.

    Thanks to `Paul Brown <http://www.paulsprogrammingnotes.com/>`__.

    * Dashboard: http://www.eventbrite.com/myaccount/apps/
    * Docs: https://developer.eventbrite.com/docs/auth/
    * API: http://developer.eventbrite.com/docs/

    Supported :class:`.User` properties:

    * email
    * first_name
    * id
    * last_name
    * name

    Unsupported :class:`.User` properties:

    * birth_date
    * city
    * country
    * gender
    * link
    * locale
    * nickname
    * phone
    * picture
    * postal_code
    * timezone
    * username

    """

    user_authorization_url = 'https://www.eventbrite.com/oauth/authorize'
    access_token_url = 'https://www.eventbrite.com/oauth/token'
    user_info_url = 'https://www.eventbriteapi.com/v3/users/me'

    supported_user_attributes = core.SupportedUserAttributes(
        email=True,
        first_name=True,
        id=True,
        last_name=True,
        name=True,
    )

    @classmethod
    def _x_credentials_parser(cls, credentials, data):
        if data.get('token_type') == 'bearer':
            credentials.token_type = cls.BEARER
        return credentials

    @staticmethod
    def _x_user_parser(user, data):
        for email in data.get('emails', []):
            if email.get('primary'):
                user.email = email.get('email')
                break

        return user


class Facebook(OAuth2):
    """
    Facebook |oauth2| provider.

    * Dashboard: https://developers.facebook.com/apps
    * Docs: http://developers.facebook.com/docs/howtos/login/server-side-login/
    * API reference: http://developers.facebook.com/docs/reference/api/
    * API explorer: http://developers.facebook.com/tools/explorer

    Supported :class:`.User` properties:

    * birth_date
    * email
    * first_name
    * id
    * last_name
    * name
    * picture

    Unsupported :class:`.User` properties:

    * nickname
    * phone
    * postal_code
    * username

    """
    user_authorization_url = 'https://www.facebook.com/dialog/oauth'
    access_token_url = 'https://graph.facebook.com/oauth/access_token'
    user_info_url = 'https://graph.facebook.com/v2.3/me'
    user_info_scope = ['email', 'public_profile', 'user_birthday',
                       'user_location']
    same_origin = False

    supported_user_attributes = core.SupportedUserAttributes(
        birth_date=True,
        city=False,
        country=False,
        email=True,
        first_name=True,
        gender=False,
        id=True,
        last_name=True,
        link=False,
        locale=False,
        location=False,
        name=True,
        picture=True,
        timezone=False,
        username=False,
    )

    @classmethod
    def _x_request_elements_filter(cls, request_type, request_elements,
                                   credentials):

        if request_type == cls.REFRESH_TOKEN_REQUEST_TYPE:
            # As always, Facebook has it's original name for "refresh_token"!
            url, method, params, headers, body = request_elements
            params['fb_exchange_token'] = params.pop('refresh_token')
            params['grant_type'] = 'fb_exchange_token'
            request_elements = core.RequestElements(url, method, params,
                                                    headers, body)

        return request_elements

    def __init__(self, *args, **kwargs):
        super(Facebook, self).__init__(*args, **kwargs)

        # Handle special Facebook requirements to be able
        # to refresh the access token.
        if self.offline:
            # Facebook needs an offline_access scope.
            if 'offline_access' not in self.scope:
                self.scope.append('offline_access')

        if self.popup:
            self.user_authorization_url += '?display=popup'

    @staticmethod
    def _x_user_parser(user, data):
        _birth_date = data.get('birthday')
        if _birth_date:
            try:
                user.birth_date = datetime.datetime.strptime(_birth_date,
                                                             '%m/%d/%Y')
            except ValueError:
                pass

        user.picture = ('http://graph.facebook.com/{0}/picture?type=large'
                        .format(user.id))

        user.location = data.get('location', {}).get('name')
        if user.location:
            split_location = user.location.split(', ')
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

        if data.get('token_type') == 'bearer':
            # TODO: cls is not available here, hardcode for now.
            credentials.token_type = 'Bearer'

        return credentials

    @staticmethod
    def _x_refresh_credentials_if(credentials):
        # Always refresh.
        return True

    def access(self, url, params=None, **kwargs):
        if params is None:
            params = {}
        params['fields'] = 'id,first_name,last_name,picture,email,gender,' + \
                           'timezone,location,birthday,locale'

        return super(Facebook, self).access(url, params, **kwargs)


class Foursquare(OAuth2):
    """
    Foursquare |oauth2| provider.

    * Dashboard: https://foursquare.com/developers/apps
    * Docs: https://developer.foursquare.com/overview/auth.html
    * API reference: https://developer.foursquare.com/docs/

    .. note::

        Foursquare requires a *version* parameter in each request.
        The default value is ``v=20140501``. You can override the version in
        the ``params`` parameter of the :meth:`.Authomatic.access` method.
        See https://developer.foursquare.com/overview/versioning

    Supported :class:`.User` properties:

    * city
    * country
    * email
    * first_name
    * gender
    * id
    * last_name
    * location
    * name
    * phone
    * picture

    Unsupported :class:`.User` properties:

    * birth_date
    * link
    * locale
    * nickname
    * postal_code
    * timezone
    * username

    """

    user_authorization_url = 'https://foursquare.com/oauth2/authenticate'
    access_token_url = 'https://foursquare.com/oauth2/access_token'
    user_info_url = 'https://api.foursquare.com/v2/users/self'

    same_origin = False

    supported_user_attributes = core.SupportedUserAttributes(
        birth_date=True,
        city=True,
        country=True,
        email=True,
        first_name=True,
        gender=True,
        id=True,
        last_name=True,
        location=True,
        name=True,
        phone=True,
        picture=True
    )

    @classmethod
    def _x_request_elements_filter(cls, request_type, request_elements,
                                   credentials):

        if request_type == cls.PROTECTED_RESOURCE_REQUEST_TYPE:
            # Foursquare uses OAuth 1.0 "oauth_token" for what should be
            # "access_token" in OAuth 2.0!
            url, method, params, headers, body = request_elements
            params['oauth_token'] = params.pop('access_token')

            # Foursquare needs the version "v" parameter in every request.
            # https://developer.foursquare.com/overview/versioning
            if not params.get('v'):
                params['v'] = '20140501'

            request_elements = core.RequestElements(url, method, params,
                                                    headers, body)

        return request_elements

    @staticmethod
    def _x_user_parser(user, data):

        _resp = data.get('response', {})
        _user = _resp.get('user', {})

        user.id = _user.get('id')
        user.first_name = _user.get('firstName')
        user.last_name = _user.get('lastName')
        user.gender = _user.get('gender')

        _birth_date = _user.get('birthday')
        if _birth_date:
            user.birth_date = datetime.datetime.fromtimestamp(_birth_date)

        _photo = _user.get('photo', {})
        if isinstance(_photo, dict):
            _photo_prefix = _photo.get('prefix', '').strip('/')
            _photo_suffix = _photo.get('suffix', '').strip('/')
            user.picture = '/'.join([_photo_prefix, _photo_suffix])

        if isinstance(_photo, str):
            user.picture = _photo

        user.location = _user.get('homeCity')
        if user.location:
            split_location = user.location.split(',')
            user.city = split_location[0].strip()
            if len(user.location) > 1:
                user.country = split_location[1].strip()

        _contact = _user.get('contact', {})
        user.email = _contact.get('email')
        user.phone = _contact.get('phone')

        return user


class GitHub(OAuth2):
    """
    GitHub |oauth2| provider.

    * Dashboard: https://github.com/settings/developers
    * Docs: http://developer.github.com/v3/#authentication
    * API reference: http://developer.github.com/v3/

    .. note::

        GitHub API
        
        Users may not have a public email address. In order to obtain the private email address, the `documentation <https://developer.github.com/v3/users/emails/#list-email-addresses-for-a-user>`_
        specifies to request ``user:email`` scope. This allows the ``default`` function to scrape ``users/email`` API endpoint.

            You can set the ``user:email`` scope like this:

        .. code-block:: python
            :emphasize-lines: 6

            CONFIG = {
                'github': {
                    'class_': oauth2.GitHub,
                    'consumer_key': '#####',
                    'consumer_secret': '#####',
                    'scope': ['user:email']
                }
            }

    Supported :class:`.User` properties:

    * email
    * id
    * link
    * location
    * name
    * picture
    * username

    Unsupported :class:`.User` properties:

    * birth_date
    * city
    * country
    * first_name
    * gender
    * last_name
    * locale
    * nickname
    * phone
    * postal_code
    * timezone

    """

    user_authorization_url = 'https://github.com/login/oauth/authorize'
    access_token_url = 'https://github.com/login/oauth/access_token'
    user_info_url = 'https://api.github.com/user'

    same_origin = False

    supported_user_attributes = core.SupportedUserAttributes(
        email=True,
        id=True,
        link=True,
        location=True,
        name=True,
        picture=True,
        username=True
    )

    @staticmethod
    def _x_user_parser(user, data):
        user.username = data.get('login')
        user.picture = data.get('avatar_url')
        user.link = data.get('html_url')
        return user

    @classmethod
    def _x_credentials_parser(cls, credentials, data):
        if data.get('token_type') == 'bearer':
            credentials.token_type = cls.BEARER
        return credentials

    def access(self, url, **kwargs):
        # https://developer.github.com/v3/#user-agent-required
        # Github requries that all API requests MUST include a valid ``User-Agent`` header.
        headers = kwargs["headers"] = kwargs.get("headers", {})
        if not headers.get("User-Agent"):
            headers["User-Agent"] = self.settings.config[self.name]["consumer_key"]

        def parent_access(url):
            return super(GitHub, self).access(url, **kwargs)

        response = parent_access(url)

        # additional action to get email is required:
        # https://developer.github.com/v3/users/emails/
        if response.status == 200:
            email_response = parent_access(url + "/emails")
            if email_response.status == 200:
                response.data["emails"] = email_response.data

                # find first or primary email
                primary_email = None
                for item in email_response.data:
                    is_primary = item["primary"]
                    if not primary_email or is_primary:
                        primary_email = item["email"]

                    if is_primary:
                        break

                response.data["email"] = primary_email
        return response


class Google(OAuth2):
    """
    Google |oauth2| provider.

    * Dashboard: https://console.developers.google.com/project
    * Docs: https://developers.google.com/accounts/docs/OAuth2
    * API reference: https://developers.google.com/gdata/docs/directory
    * API explorer: https://developers.google.com/oauthplayground/

    Supported :class:`.User` properties:

    * email
    * first_name
    * gender
    * id
    * last_name
    * link
    * locale
    * name
    * picture

    Unsupported :class:`.User` properties:

    * birth_date
    * city
    * country
    * nickname
    * phone
    * postal_code
    * timezone
    * username

    .. note::

        To get the user info, you need to activate the **Google+ API**
        in the **APIs & auth >> APIs** section of the`Google Developers Console
        <https://console.developers.google.com/project>`__.

    """

    user_authorization_url = 'https://accounts.google.com/o/oauth2/auth'
    access_token_url = 'https://accounts.google.com/o/oauth2/token'
    user_info_url = 'https://www.googleapis.com/oauth2/v3/userinfo?alt=json'

    user_info_scope = ['profile',
                       'email']

    supported_user_attributes = core.SupportedUserAttributes(
        id=True,
        email=True,
        name=True,
        first_name=True,
        last_name=True,
        locale=True,
        picture=True
    )

    def __init__(self, *args, **kwargs):
        super(Google, self).__init__(*args, **kwargs)

        # Handle special Google requirements to be able to refresh the access
        # token.
        if self.offline:
            if 'access_type' not in self.user_authorization_params:
                # Google needs access_type=offline param in the user
                # authorization request.
                self.user_authorization_params['access_type'] = 'offline'
            if 'approval_prompt' not in self.user_authorization_params:
                # And also approval_prompt=force.
                self.user_authorization_params['approval_prompt'] = 'force'

    @classmethod
    def _x_request_elements_filter(cls, request_type, request_elements,
                                   credentials):
        """
        Google doesn't accept client ID and secret to be at the same time in
        request parameters and in the basic authorization header in the access
        token request.
        """
        if request_type is cls.ACCESS_TOKEN_REQUEST_TYPE:
            params = request_elements[2]
            del params['client_id']
            del params['client_secret']
        return request_elements

    @staticmethod
    def _x_user_parser(user, data):
        emails = data.get('emails', [])
        if emails:
            user.email = emails[0].get('value')
            for email in emails:
                if email.get('type') == 'account':
                    user.email = email.get('value')
                    break

        user.id = data.get('sub')
        user.name = data.get('name')
        user.first_name = data.get('given_name', '')
        user.last_name = data.get('family_name', '')
        user.locale = data.get('locale', '')
        user.picture = data.get('picture', '')

        user.email_verified = data.get("email_verified")
        user.hosted_domain = data.get("hd")
        return user

    def _x_scope_parser(self, scope):
        """
        Google has space-separated scopes.
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

    Supported :class:`.User` properties:

    * city
    * country
    * email
    * first_name
    * id
    * last_name
    * link
    * name
    * picture

    Unsupported :class:`.User` properties:

    * birth_date
    * gender
    * locale
    * location
    * nickname
    * phone
    * postal_code
    * timezone
    * username

    """

    user_authorization_url = 'https://www.linkedin.com/uas/oauth2/' + \
                             'authorization'
    access_token_url = 'https://www.linkedin.com/uas/oauth2/accessToken'
    user_info_url = ('https://api.linkedin.com/v1/people/~:'
                     '(id,first-name,last-name,formatted-name,location,'
                     'picture-url,public-profile-url,email-address)'
                     '?format=json')

    user_info_scope = ['r_emailaddress']

    token_request_method = 'GET'  # To avoid a bug with OAuth2.0 on Linkedin
    # http://developer.linkedin.com/forum/unauthorized-invalid-or-expired-token-immediately-after-receiving-oauth2-token

    supported_user_attributes = core.SupportedUserAttributes(
        city=True,
        country=True,
        email=True,
        first_name=True,
        id=True,
        last_name=True,
        link=True,
        location=False,
        name=True,
        picture=True
    )

    @classmethod
    def _x_request_elements_filter(cls, request_type, request_elements,
                                   credentials):
        if request_type == cls.PROTECTED_RESOURCE_REQUEST_TYPE:
            # LinkedIn too has it's own terminology!
            url, method, params, headers, body = request_elements
            params['oauth2_access_token'] = params.pop('access_token')
            request_elements = core.RequestElements(url, method, params,
                                                    headers, body)

        return request_elements

    @staticmethod
    def _x_user_parser(user, data):

        user.first_name = data.get('firstName')
        user.last_name = data.get('lastName')
        user.email = data.get('emailAddress')
        user.name = data.get('formattedName')
        user.city = user.city = data.get('location', {}).get('name')
        user.country = data.get('location', {}).get('country', {}).get('code')
        user.phone = data.get('phoneNumbers', {}).get('values', [{}])[0]\
            .get('phoneNumber')
        user.picture = data.get('pictureUrl')
        user.link = data.get('publicProfileUrl')

        _birthdate = data.get('dateOfBirth', {})
        if _birthdate:
            _day = _birthdate.get('day')
            _month = _birthdate.get('month')
            _year = _birthdate.get('year')
            if _day and _month and _year:
                user.birth_date = datetime.datetime(_year, _month, _day)

        return user


class PayPal(OAuth2):
    """
    PayPal |oauth2| provider.

    * Dashboard: https://developer.paypal.com/webapps/developer/applications
    * Docs: https://developer.paypal.com/webapps/developer/docs/integration/direct/make-your-first-call/
    * API reference: https://developer.paypal.com/webapps/developer/docs/api/

    .. note::

        Paypal doesn't redirect the **user** to authorize your app!
        It grants you an **access token** based on your **app's** key and
        secret instead.

    """

    _x_use_authorization_header = True

    supported_user_attributes = core.SupportedUserAttributes()

    @classmethod
    def _x_request_elements_filter(
            cls, request_type, request_elements, credentials):

        if request_type == cls.ACCESS_TOKEN_REQUEST_TYPE:
            url, method, params, headers, body = request_elements
            params['grant_type'] = 'client_credentials'
            request_elements = core.RequestElements(
                url, method, params, headers, body)

        return request_elements

    user_authorization_url = ''
    access_token_url = 'https://api.sandbox.paypal.com/v1/oauth2/token'
    user_info_url = ''


class Reddit(OAuth2):
    """
    Reddit |oauth2| provider.

    .. note::

        Currently credentials refreshment returns
        ``{"error": "invalid_request"}``.

    * Dashboard: https://ssl.reddit.com/prefs/apps
    * Docs: https://github.com/reddit/reddit/wiki/OAuth2
    * API reference: http://www.reddit.com/dev/api

    .. note::

        According to
        `Reddit API docs <https://github.com/reddit/reddit/wiki/API#rules>`_,
        you have to include a `User-Agent` header in each API call.

        You can apply a default ``User-Agent`` header for all API calls in the
        config like this:

        .. code-block:: python
            :emphasize-lines: 6

            CONFIG = {
                'reddit': {
                    'class_': oauth2.Reddit,
                    'consumer_key': '#####',
                    'consumer_secret': '#####',
                    'access_headers': {'User-Agent': "Andy Pipkin's App"},
                }
            }

    Supported :class:`.User` properties:

    * id
    * username

    Unsupported :class:`.User` properties:

    * birth_date
    * country
    * city
    * email
    * first_name
    * gender
    * last_name
    * link
    * locale
    * location
    * name
    * nickname
    * phone
    * picture
    * postal_code
    * timezone

    """

    user_authorization_url = 'https://ssl.reddit.com/api/v1/authorize'
    access_token_url = 'https://ssl.reddit.com/api/v1/access_token'
    user_info_url = 'https://oauth.reddit.com/api/v1/me.json'

    user_info_scope = ['identity']

    supported_user_attributes = core.SupportedUserAttributes(
        id=True,
        name=True,
        username=True
    )

    def __init__(self, *args, **kwargs):
        super(Reddit, self).__init__(*args, **kwargs)

        if self.offline:
            if 'duration' not in self.user_authorization_params:
                # http://www.reddit.com/r/changelog/comments/11jab9/reddit_change_permanent_oauth_grants_using/
                self.user_authorization_params['duration'] = 'permanent'

    @classmethod
    def _x_credentials_parser(cls, credentials, data):
        if data.get('token_type') == 'bearer':
            credentials.token_type = cls.BEARER
        return credentials

    @staticmethod
    def _x_user_parser(user, data):
        user.username = data.get('name')
        return user


class Viadeo(OAuth2):
    """
    Viadeo |oauth2| provider.

    .. note::

        As stated in the `Viadeo documentation
        <http://dev.viadeo.com/documentation/authentication/request-an-api-key/>`__:

            Viadeo restrains access to its API.
            They are now exclusively reserved for its strategic partners.

    * Dashboard: http://dev.viadeo.com/dashboard/
    * Docs:
      http://dev.viadeo.com/documentation/authentication/oauth-authentication/
    * API reference: http://dev.viadeo.com/documentation/

    .. note::

        Viadeo doesn't support **credentials refreshment**.
        As stated in their
        `docs
        <http://dev.viadeo.com/documentation/authentication/oauth-authentication/>`_:
        "The access token has an infinite time to live."

    """

    user_authorization_url = 'https://secure.viadeo.com/oauth-provider/' + \
                             'authorize2'
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

    * Dashboard: http://vk.com/apps?act=manage
    * Docs: http://vk.com/developers.php?oid=-17680044&p=Authorizing_Sites
    * API reference: http://vk.com/developers.php?oid=-17680044&p=API_
      Method_Description

    .. note::

        VK uses a
        `bitmask scope
        <http://vk.com/developers.php?oid=-17680044&p=Application_Rights>`_!
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

    Supported :class:`.User` properties:

    * birth_date
    * city
    * country
    * first_name
    * gender
    * id
    * last_name
    * location
    * name
    * picture
    * timezone

    Unsupported :class:`.User` properties:

    * email
    * link
    * locale
    * nickname
    * phone
    * postal_code
    * username

    """

    user_authorization_url = 'http://api.vkontakte.ru/oauth/authorize'
    access_token_url = 'https://api.vkontakte.ru/oauth/access_token'
    user_info_url = 'https://api.vk.com/method/getProfiles?' + \
                    'fields=uid,first_name,last_name,nickname,sex,bdate,' + \
                    'city,country,timezone,photo_big'

    supported_user_attributes = core.SupportedUserAttributes(
        birth_date=True,
        city=True,
        country=True,
        first_name=True,
        gender=True,
        id=True,
        last_name=True,
        location=True,
        name=True,
        picture=True,
        timezone=True,
    )

    def __init__(self, *args, **kwargs):
        super(VK, self).__init__(*args, **kwargs)

        if self.offline:
            if 'offline' not in self.scope:
                self.scope.append('offline')

    @staticmethod
    def _x_user_parser(user, data):
        _resp = data.get('response', [{}])[0]

        _birth_date = _resp.get('bdate')
        if _birth_date:
            user.birth_date = datetime.datetime.strptime(
                _birth_date, '%d.%m.%Y')
        user.id = _resp.get('uid')
        user.first_name = _resp.get('first_name')
        user.gender = _resp.get('sex')
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

    * Dashboard: https://account.live.com/developers/applications
    * Docs: http://msdn.microsoft.com/en-us/library/hh243647.aspx
    * API explorer: http://isdk.dev.live.com/?mkt=en-us

    Supported :class:`.User` properties:

    * email
    * first_name
    * id
    * last_name
    * link
    * locale
    * name
    * picture

    Unsupported :class:`.User` properties:

    * birth_date
    * city
    * country
    * gender
    * nickname
    * location
    * phone
    * postal_code
    * timezone
    * username

    """

    user_authorization_url = 'https://login.live.com/oauth20_authorize.srf'
    access_token_url = 'https://login.live.com/oauth20_token.srf'
    user_info_url = 'https://apis.live.net/v5.0/me'

    user_info_scope = ['wl.basic', 'wl.emails', 'wl.photos']

    supported_user_attributes = core.SupportedUserAttributes(
        email=True,
        first_name=True,
        id=True,
        last_name=True,
        link=True,
        locale=True,
        name=True,
        picture=True
    )

    def __init__(self, *args, **kwargs):
        super(WindowsLive, self).__init__(*args, **kwargs)

        if self.offline:
            if 'wl.offline_access' not in self.scope:
                self.scope.append('wl.offline_access')

    @classmethod
    def _x_credentials_parser(cls, credentials, data):
        if data.get('token_type') == 'bearer':
            credentials.token_type = cls.BEARER
        return credentials

    @staticmethod
    def _x_user_parser(user, data):
        user.email = data.get('emails', {}).get('preferred')
        user.picture = 'https://apis.live.net/v5.0/{0}/picture'.format(
            data.get('id'))
        return user


class Yammer(OAuth2):
    """
    Yammer |oauth2| provider.

    * Dashboard: https://www.yammer.com/client_applications
    * Docs: https://developer.yammer.com/authentication/
    * API reference: https://developer.yammer.com/restapi/

    Supported :class:`.User` properties:

    * birth_date
    * city
    * country
    * email
    * first_name
    * id
    * last_name
    * link
    * locale
    * location
    * name
    * phone
    * picture
    * timezone
    * username

    Unsupported :class:`.User` properties:

    * gender
    * nickname
    * postal_code

    """

    user_authorization_url = 'https://www.yammer.com/dialog/oauth'
    access_token_url = 'https://www.yammer.com/oauth2/access_token.json'
    user_info_url = 'https://www.yammer.com/api/v1/users/current.json'

    supported_user_attributes = core.SupportedUserAttributes(
        birth_date=True,
        city=True,
        country=True,
        email=True,
        first_name=True,
        id=True,
        last_name=True,
        link=True,
        locale=True,
        location=True,
        name=True,
        phone=True,
        picture=True,
        timezone=True,
        username=True
    )

    @classmethod
    def _x_credentials_parser(cls, credentials, data):
        # import pdb; pdb.set_trace()
        credentials.token_type = cls.BEARER
        _access_token = data.get('access_token', {})
        credentials.token = _access_token.get('token')
        _expire_in = _access_token.get('expires_at', 0)
        if _expire_in:
            credentials.expire_in = _expire_in
        return credentials

    @staticmethod
    def _x_user_parser(user, data):

        # Yammer provides most of the user info in the access token request,
        # but provides more on in user info request.
        _user = data.get('user', {})
        if not _user:
            # If there is "user key", it is token request.
            _user = data

        user.username = _user.get('name')
        user.name = _user.get('full_name')
        user.link = _user.get('web_url')
        user.picture = _user.get('mugshot_url')

        user.city, user.country = _user.get('location', ',').split(',')
        user.city = user.city.strip()
        user.country = user.country.strip()
        user.locale = _user.get('web_preferences', {}).get('locale')

        # Contact
        _contact = _user.get('contact', {})
        user.phone = _contact.get('phone_numbers', [{}])[0].get('number')
        _emails = _contact.get('email_addresses', [])
        for email in _emails:
            if email.get('type', '') == 'primary':
                user.email = email.get('address')
                break

        try:
            user.birth_date = datetime.datetime.strptime(
                _user.get('birth_date'), "%B %d")
        except ValueError:
            user.birth_date = _user.get('birth_date')

        return user


class Yandex(OAuth2):
    """
    Yandex |oauth2| provider.

    * Dashboard: https://oauth.yandex.com/client/my
    * Docs: http://api.yandex.com/oauth/doc/dg/reference/obtain-access-token.xml
    * API reference:

    Supported :class:`.User` properties:

    * id
    * name
    * username

    Unsupported :class:`.User` properties:

    * birth_date
    * city
    * country
    * email
    * first_name
    * gender
    * last_name
    * link
    * locale
    * location
    * nickname
    * phone
    * picture
    * postal_code
    * timezone

    """

    user_authorization_url = 'https://oauth.yandex.com/authorize'
    access_token_url = 'https://oauth.yandex.com/token'
    user_info_url = 'https://login.yandex.ru/info'

    supported_user_attributes = core.SupportedUserAttributes(
        id=True,
        name=True,
        username=True
    )

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
        user.username = data.get('login')

        try:
            user.birth_date = datetime.datetime.strptime(
                data.get('birthday'), "%Y-%m-%d")
        except ValueError:
            user.birth_date = data.get('birthday')

        return user


# The provider type ID is generated from this list's indexes!
# Always append new providers at the end so that ids of existing providers
# don't change!
PROVIDER_ID_MAP = [
    Amazon,
    Behance,
    Bitly,
    Cosm,
    DeviantART,
    Eventbrite,
    Facebook,
    Foursquare,
    GitHub,
    Google,
    LinkedIn,
    OAuth2,
    PayPal,
    Reddit,
    Viadeo,
    VK,
    WindowsLive,
    Yammer,
    Yandex,
]
