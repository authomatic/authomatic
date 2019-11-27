# -*- coding: utf-8 -*-
"""
|oauth1| Providers
--------------------

Providers which implement the |oauth1|_ protocol.

.. autosummary::

    OAuth1
    Bitbucket
    Flickr
    Meetup
    Plurk
    Twitter
    Tumblr
    UbuntuOne
    Vimeo
    Xero
    Xing
    Yahoo

"""

import abc
import binascii
import datetime
import hashlib
import hmac
import logging
import time
import uuid

import authomatic.core as core
from authomatic import providers
from authomatic.exceptions import (
    CancellationError,
    FailureError,
    OAuth1Error,
)
from authomatic import six
from authomatic.six.moves import urllib_parse as parse


__all__ = [
    'OAuth1',
    'Bitbucket',
    'Flickr',
    'Meetup',
    'Plurk',
    'Twitter',
    'Tumblr',
    'UbuntuOne',
    'Vimeo',
    'Xero',
    'Xing',
    'Yahoo'
]


def _normalize_params(params):
    """
    Returns a normalized query string sorted first by key, then by value
    excluding the ``realm`` and ``oauth_signature`` parameters as specified
    here: http://oauth.net/core/1.0a/#rfc.section.9.1.1.

    :param params:
        :class:`dict` or :class:`list` of tuples.

    """

    if isinstance(params, dict):
        params = list(params.items())

    # remove "realm" and "oauth_signature"
    params = sorted([
        (k, v) for k, v in params
        if k not in ('oauth_signature', 'realm')
    ])
    # sort
    # convert to query string
    qs = parse.urlencode(params)
    # replace "+" to "%20"
    qs = qs.replace('+', '%20')
    # replace "%7E" to "%20"
    qs = qs.replace('%7E', '~')

    return qs


def _join_by_ampersand(*args):
    return '&'.join([core.escape(i) for i in args])


def _create_base_string(method, base, params):
    """
    Returns base string for HMAC-SHA1 signature as specified in:
    http://oauth.net/core/1.0a/#rfc.section.9.1.3.
    """

    normalized_qs = _normalize_params(params)
    return _join_by_ampersand(method, base, normalized_qs)


class BaseSignatureGenerator(object):
    """
    Abstract base class for all signature generators.
    """

    __metaclass__ = abc.ABCMeta

    #: :class:`str` The name of the signature method.
    method = ''

    @abc.abstractmethod
    def create_signature(self, method, base, params,
                         consumer_secret, token_secret=''):
        """
        Must create signature based on the parameters as specified in
        http://oauth.net/core/1.0a/#signing_process.

        .. warning::

            |classmethod|

        :param str method:
            HTTP method of the request to be signed.

        :param str base:
            Base URL of the request without query string an fragment.

        :param dict params:
            Dictionary or list of tuples of the request parameters.

        :param str consumer_secret:
            :attr:`.core.Consumer.secret`

        :param str token_secret:
            Access token secret as specified in
            http://oauth.net/core/1.0a/#anchor3.

        :returns:
            The signature string.

        """


class HMACSHA1SignatureGenerator(BaseSignatureGenerator):
    """
    HMAC-SHA1 signature generator.

    See: http://oauth.net/core/1.0a/#anchor15

    """

    method = 'HMAC-SHA1'

    @classmethod
    def _create_key(cls, consumer_secret, token_secret=''):
        """
        Returns a key for HMAC-SHA1 signature as specified at:
        http://oauth.net/core/1.0a/#rfc.section.9.2.

        :param str consumer_secret:
            :attr:`.core.Consumer.secret`

        :param str token_secret:
            Access token secret as specified in
            http://oauth.net/core/1.0a/#anchor3.

        :returns:
            Key to sign the request with.

        """

        return _join_by_ampersand(consumer_secret, token_secret or '')

    @classmethod
    def create_signature(cls, method, base, params,
                         consumer_secret, token_secret=''):
        """
        Returns HMAC-SHA1 signature as specified at:
        http://oauth.net/core/1.0a/#rfc.section.9.2.

        :param str method:
            HTTP method of the request to be signed.

        :param str base:
            Base URL of the request without query string an fragment.

        :param dict params:
            Dictionary or list of tuples of the request parameters.

        :param str consumer_secret:
            :attr:`.core.Consumer.secret`

        :param str token_secret:
            Access token secret as specified in
            http://oauth.net/core/1.0a/#anchor3.

        :returns:
            The signature string.

        """

        base_string = _create_base_string(method, base, params)
        key = cls._create_key(consumer_secret, token_secret)

        hashed = hmac.new(
            six.b(key),
            base_string.encode('utf-8'),
            hashlib.sha1)

        base64_encoded = binascii.b2a_base64(hashed.digest())[:-1]

        return base64_encoded


class PLAINTEXTSignatureGenerator(BaseSignatureGenerator):
    """
    PLAINTEXT signature generator.

    See: http://oauth.net/core/1.0a/#anchor21

    """

    method = 'PLAINTEXT'

    @classmethod
    def create_signature(cls, method, base, params,
                         consumer_secret, token_secret=''):

        consumer_secret = parse.quote(consumer_secret, '')
        token_secret = parse.quote(token_secret, '')

        return parse.quote('&'.join((consumer_secret, token_secret)), '')


class OAuth1(providers.AuthorizationProvider):
    """
    Base class for |oauth1|_ providers.
    """

    _signature_generator = HMACSHA1SignatureGenerator

    PROVIDER_TYPE_ID = 1
    REQUEST_TOKEN_REQUEST_TYPE = 1

    def __init__(self, *args, **kwargs):
        """
        Accepts additional keyword arguments:

        :param str consumer_key:
            The *key* assigned to our application (**consumer**) by
            the **provider**.

        :param str consumer_secret:
            The *secret* assigned to our application (**consumer**) by
            the **provider**.

        :param id:
            A unique short name used to serialize :class:`.Credentials`.

        :param dict user_authorization_params:
            A dictionary of additional request parameters for
            **user authorization request**.

        :param dict access_token_params:
            A dictionary of additional request parameters for
            **access token request**.

        :param dict request_token_params:
            A dictionary of additional request parameters for
            **request token request**.

        """

        super(OAuth1, self).__init__(*args, **kwargs)

        self.request_token_params = self._kwarg(
            kwargs, 'request_token_params', {})

    # ========================================================================
    # Abstract properties
    # ========================================================================

    @abc.abstractproperty
    def request_token_url(self):
        """
        :class:`str` URL where we can get the |oauth1| request token.
        see http://oauth.net/core/1.0a/#auth_step1.
        """

    # ========================================================================
    # Internal methods
    # ========================================================================

    @classmethod
    def create_request_elements(
            cls, request_type, credentials, url, params=None, headers=None,
            body='', method='GET', verifier='', callback=''
    ):
        """
        Creates |oauth1| request elements.
        """

        params = params or {}
        headers = headers or {}

        consumer_key = credentials.consumer_key or ''
        consumer_secret = credentials.consumer_secret or ''
        token = credentials.token or ''
        token_secret = credentials.token_secret or ''

        # separate url base and query parameters
        url, base_params = cls._split_url(url)

        # add extracted params to future params
        params.update(dict(base_params))

        if request_type == cls.USER_AUTHORIZATION_REQUEST_TYPE:
            # no need for signature
            if token:
                params['oauth_token'] = token
            else:
                raise OAuth1Error(
                    'Credentials with valid token are required to create '
                    'User Authorization URL!')
        else:
            # signature needed
            if request_type == cls.REQUEST_TOKEN_REQUEST_TYPE:
                # Request Token URL
                if consumer_key and consumer_secret and callback:
                    params['oauth_consumer_key'] = consumer_key
                    params['oauth_callback'] = callback
                else:
                    raise OAuth1Error(
                        'Credentials with valid consumer_key, consumer_secret '
                        'and callback are required to create Request Token '
                        'URL!')

            elif request_type == cls.ACCESS_TOKEN_REQUEST_TYPE:
                # Access Token URL
                if consumer_key and consumer_secret and token and verifier:
                    params['oauth_token'] = token
                    params['oauth_consumer_key'] = consumer_key
                    params['oauth_verifier'] = verifier
                else:
                    raise OAuth1Error(
                        'Credentials with valid consumer_key, '
                        'consumer_secret, token and argument verifier'
                        ' are required to create Access Token URL!')

            elif request_type == cls.PROTECTED_RESOURCE_REQUEST_TYPE:
                # Protected Resources URL
                if consumer_key and consumer_secret and token and token_secret:
                    params['oauth_token'] = token
                    params['oauth_consumer_key'] = consumer_key
                else:
                    raise OAuth1Error(
                        'Credentials with valid consumer_key, '
                        'consumer_secret, token and token_secret are required '
                        'to create Protected Resources URL!')

            # Sign request.
            # http://oauth.net/core/1.0a/#anchor13

            # Prepare parameters for signature base string
            # http://oauth.net/core/1.0a/#rfc.section.9.1
            params['oauth_signature_method'] = cls._signature_generator.method
            params['oauth_timestamp'] = str(int(time.time()))
            params['oauth_nonce'] = cls.csrf_generator(str(uuid.uuid4()))
            params['oauth_version'] = '1.0'

            # add signature to params
            params['oauth_signature'] = cls._signature_generator.create_signature(  # noqa
                method, url, params, consumer_secret, token_secret)

        request_elements = core.RequestElements(
            url, method, params, headers, body)

        return cls._x_request_elements_filter(
            request_type, request_elements, credentials)

    # ========================================================================
    # Exposed methods
    # ========================================================================

    @staticmethod
    def to_tuple(credentials):
        return (credentials.token, credentials.token_secret)

    @classmethod
    def reconstruct(cls, deserialized_tuple, credentials, cfg):

        token, token_secret = deserialized_tuple

        credentials.token = token
        credentials.token_secret = token_secret
        credentials.consumer_key = cfg.get('consumer_key', '')
        credentials.consumer_secret = cfg.get('consumer_secret', '')

        return credentials

    @providers.login_decorator
    def login(self):
        # get request parameters from which we can determine the login phase
        denied = self.params.get('denied')
        verifier = self.params.get('oauth_verifier', '')
        request_token = self.params.get('oauth_token', '')

        if request_token and verifier:
            # Phase 2 after redirect with success
            self._log(
                logging.INFO,
                u'Continuing OAuth 1.0a authorization procedure after '
                u'redirect.')
            token_secret = self._session_get('token_secret')
            if not token_secret:
                raise FailureError(
                    u'Unable to retrieve token secret from storage!')

            # Get Access Token
            self._log(
                logging.INFO,
                u'Fetching for access token from {0}.'.format(
                    self.access_token_url))

            self.credentials.token = request_token
            self.credentials.token_secret = token_secret

            request_elements = self.create_request_elements(
                request_type=self.ACCESS_TOKEN_REQUEST_TYPE,
                url=self.access_token_url,
                credentials=self.credentials,
                verifier=verifier,
                params=self.access_token_params
            )

            response = self._fetch(*request_elements)
            self.access_token_response = response

            if not self._http_status_in_category(response.status, 2):
                raise FailureError(
                    'Failed to obtain OAuth 1.0a  oauth_token from {0}! '
                    'HTTP status code: {1}.'
                    .format(self.access_token_url, response.status),
                    original_message=response.content,
                    status=response.status,
                    url=self.access_token_url
                )

            self._log(logging.INFO, u'Got access token.')
            self.credentials.token = response.data.get('oauth_token', '')
            self.credentials.token_secret = response.data.get(
                'oauth_token_secret', ''
            )

            self.credentials = self._x_credentials_parser(self.credentials,
                                                          response.data)
            self._update_or_create_user(response.data, self.credentials)

            # =================================================================
            # We're done!
            # =================================================================

        elif denied:
            # Phase 2 after redirect denied
            raise CancellationError(
                'User denied the request token {0} during a redirect'
                'to {1}!'.format(denied, self.user_authorization_url),
                original_message=denied,
                url=self.user_authorization_url)
        else:
            # Phase 1 before redirect
            self._log(
                logging.INFO,
                u'Starting OAuth 1.0a authorization procedure.')

            # Fetch for request token
            request_elements = self.create_request_elements(
                request_type=self.REQUEST_TOKEN_REQUEST_TYPE,
                credentials=self.credentials,
                url=self.request_token_url,
                callback=self.url,
                params=self.request_token_params
            )

            self._log(
                logging.INFO,
                u'Fetching for request token and token secret.')
            response = self._fetch(*request_elements)

            # check if response status is OK
            if not self._http_status_in_category(response.status, 2):
                raise FailureError(
                    u'Failed to obtain request token from {0}! HTTP status '
                    u'code: {1} content: {2}'.format(
                        self.request_token_url,
                        response.status,
                        response.content
                    ),
                    original_message=response.content,
                    status=response.status,
                    url=self.request_token_url)

            # extract request token
            request_token = response.data.get('oauth_token')
            if not request_token:
                raise FailureError(
                    'Response from {0} doesn\'t contain oauth_token '
                    'parameter!'.format(self.request_token_url),
                    original_message=response.content,
                    url=self.request_token_url)

            # we need request token for user authorization redirect
            self.credentials.token = request_token

            # extract token secret and save it to storage
            token_secret = response.data.get('oauth_token_secret')
            if token_secret:
                # we need token secret after user authorization redirect to get
                # access token
                self._session_set('token_secret', token_secret)
            else:
                raise FailureError(
                    u'Failed to obtain token secret from {0}!'.format(
                        self.request_token_url),
                    original_message=response.content,
                    url=self.request_token_url)

            self._log(logging.INFO, u'Got request token and token secret')

            # Create User Authorization URL
            request_elements = self.create_request_elements(
                request_type=self.USER_AUTHORIZATION_REQUEST_TYPE,
                credentials=self.credentials,
                url=self.user_authorization_url,
                params=self.user_authorization_params
            )

            self._log(
                logging.INFO,
                u'Redirecting user to {0}.'.format(
                    request_elements.full_url))

            self.redirect(request_elements.full_url)


class Bitbucket(OAuth1):
    """
    Bitbucket |oauth1| provider.

    * Dashboard: https://bitbucket.org/account/user/peterhudec/api
    * Docs: https://confluence.atlassian.com/display/BITBUCKET/oauth+Endpoint
    * API reference:
      https://confluence.atlassian.com/display/BITBUCKET/Using+the+Bitbucket+REST+APIs

    Supported :class:`.User` properties:

    * first_name
    * id
    * last_name
    * link
    * name
    * picture
    * username
    * email

    Unsupported :class:`.User` properties:

    * birth_date
    * city
    * country
    * gender
    * locale
    * location
    * nickname
    * phone
    * postal_code
    * timezone

    .. note::

        To get the full user info, you need to select both the *Account Read*
        and the *Repositories Read* permission in the Bitbucket application
        edit form.

    """

    supported_user_attributes = core.SupportedUserAttributes(
        first_name=True,
        id=True,
        last_name=True,
        link=True,
        name=True,
        picture=True,
        username=True,
        email=True
    )

    request_token_url = 'https://bitbucket.org/!api/1.0/oauth/request_token'
    user_authorization_url = 'https://bitbucket.org/!api/1.0/oauth/' + \
                             'authenticate'
    access_token_url = 'https://bitbucket.org/!api/1.0/oauth/access_token'
    user_info_url = 'https://api.bitbucket.org/1.0/user'
    user_email_url = 'https://api.bitbucket.org/1.0/emails'

    @staticmethod
    def _x_user_parser(user, data):
        _user = data.get('user', {})
        user.username = user.id = _user.get('username')
        user.name = _user.get('display_name')
        user.first_name = _user.get('first_name')
        user.last_name = _user.get('last_name')
        user.picture = _user.get('avatar')
        user.link = 'https://bitbucket.org/api{0}'\
            .format(_user.get('resource_uri'))
        return user

    def _access_user_info(self):
        """
        Email is available in separate method so second request is needed.
        """
        response = super(Bitbucket, self)._access_user_info()

        response.data.setdefault("email", None)

        email_response = self.access(self.user_email_url)
        if email_response.data:
            for item in email_response.data:
                if item.get("primary", False):
                    response.data.update(email=item.get("email", None))

        return response


class Flickr(OAuth1):
    """
    Flickr |oauth1| provider.

    * Dashboard: https://www.flickr.com/services/apps/
    * Docs: https://www.flickr.com/services/api/auth.oauth.html
    * API reference: https://www.flickr.com/services/api/

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

    .. note::

        If you encounter the "Oops! Flickr doesn't recognise the
        permission set." message, you need to add the ``perms=read`` or
        ``perms=write`` parameter to the *user authorization request*.
        You can do it by adding the ``user_authorization_params``
        key to the :doc:`config`:

        .. code-block:: python
            :emphasize-lines: 6

            CONFIG = {
                'flickr': {
                    'class_': oauth1.Flickr,
                    'consumer_key': '##########',
                    'consumer_secret': '##########',
                    'user_authorization_params': dict(perms='read'),
                },
            }

    """

    supported_user_attributes = core.SupportedUserAttributes(
        id=True,
        name=True,
        username=True
    )

    request_token_url = 'http://www.flickr.com/services/oauth/request_token'
    user_authorization_url = 'http://www.flickr.com/services/oauth/authorize'
    access_token_url = 'http://www.flickr.com/services/oauth/access_token'
    user_info_url = None

    supports_jsonp = True

    @staticmethod
    def _x_user_parser(user, data):
        _user = data.get('user', {})

        user.name = data.get('fullname') or _user.get(
            'username', {}).get('_content')
        user.id = data.get('user_nsid') or _user.get('id')

        return user


class Meetup(OAuth1):
    """
    Meetup |oauth1| provider.

    .. note::

        Meetup also supports |oauth2| but you need the **user ID** to update
        the **user** info, which they don't provide in the |oauth2| access
        token response.

    * Dashboard: http://www.meetup.com/meetup_api/oauth_consumers/
    * Docs: http://www.meetup.com/meetup_api/auth/#oauth
    * API: http://www.meetup.com/meetup_api/docs/

    Supported :class:`.User` properties:

    * city
    * country
    * id
    * link
    * locale
    * location
    * name
    * picture

    Unsupported :class:`.User` properties:

    * birth_date
    * email
    * first_name
    * gender
    * last_name
    * nickname
    * phone
    * postal_code
    * timezone
    * username

    """

    supported_user_attributes = core.SupportedUserAttributes(
        city=True,
        country=True,
        id=True,
        link=True,
        locale=True,
        location=True,
        name=True,
        picture=True
    )

    request_token_url = 'https://api.meetup.com/oauth/request/'
    user_authorization_url = 'http://www.meetup.com/authorize/'
    access_token_url = 'https://api.meetup.com/oauth/access/'
    user_info_url = 'https://api.meetup.com/2/member/{id}'

    @staticmethod
    def _x_user_parser(user, data):

        user.id = data.get('id') or data.get('member_id')
        user.locale = data.get('lang')
        user.picture = data.get('photo', {}).get('photo_link')

        return user


class Plurk(OAuth1):
    """
    Plurk |oauth1| provider.

    * Dashboard: http://www.plurk.com/PlurkApp/
    * Docs:
    * API: http://www.plurk.com/API
    * API explorer: http://www.plurk.com/OAuth/test/

    Supported :class:`.User` properties:

    * birth_date
    * city
    * country
    * email
    * gender
    * id
    * link
    * locale
    * location
    * name
    * nickname
    * picture
    * timezone
    * username

    Unsupported :class:`.User` properties:

    * first_name
    * last_name
    * phone
    * postal_code

    """

    supported_user_attributes = core.SupportedUserAttributes(
        birth_date=True,
        city=True,
        country=True,
        email=True,
        gender=True,
        id=True,
        link=True,
        locale=True,
        location=True,
        name=True,
        nickname=True,
        picture=True,
        timezone=True,
        username=True
    )

    request_token_url = 'http://www.plurk.com/OAuth/request_token'
    user_authorization_url = 'http://www.plurk.com/OAuth/authorize'
    access_token_url = 'http://www.plurk.com/OAuth/access_token'
    user_info_url = 'http://www.plurk.com/APP/Profile/getOwnProfile'

    @staticmethod
    def _x_user_parser(user, data):

        _user = data.get('user_info', {})

        user.email = _user.get('email')
        user.gender = _user.get('gender')
        user.id = _user.get('id') or _user.get('uid')
        user.locale = _user.get('default_lang')
        user.name = _user.get('full_name')
        user.nickname = _user.get('nick_name')
        user.picture = 'http://avatars.plurk.com/{0}-big2.jpg'.format(user.id)
        user.timezone = _user.get('timezone')
        user.username = _user.get('display_name')

        user.link = 'http://www.plurk.com/{0}/'.format(user.username)

        user.city, user.country = _user.get('location', ',').split(',')
        user.city = user.city.strip()
        user.country = user.country.strip()

        _bd = _user.get('date_of_birth')
        if _bd:
            try:
                user.birth_date = datetime.datetime.strptime(
                    _bd,
                    "%a, %d %b %Y %H:%M:%S %Z"
                )
            except ValueError:
                pass

        return user


class Twitter(OAuth1):
    """
    Twitter |oauth1| provider.

    * Dashboard: https://dev.twitter.com/apps
    * Docs: https://dev.twitter.com/docs
    * API reference: https://dev.twitter.com/docs/api

    .. note:: To prevent multiple authorization attempts, you should enable
      the option:
      ``Allow this application to be used to Sign in with Twitter``
      in the Twitter 'Application Management' page. (http://apps.twitter.com)

    Supported :class:`.User` properties:

    * email
    * city
    * country
    * id
    * link
    * locale
    * location
    * name
    * picture
    * username

    Unsupported :class:`.User` properties:

    * birth_date
    * email
    * gender
    * first_name
    * last_name
    * locale
    * nickname
    * phone
    * postal_code
    * timezone

    """

    supported_user_attributes = core.SupportedUserAttributes(
        city=True,
        country=True,
        id=True,
        email=False,
        link=True,
        locale=False,
        location=True,
        name=True,
        picture=True,
        username=True
    )

    request_token_url = 'https://api.twitter.com/oauth/request_token'
    user_authorization_url = 'https://api.twitter.com/oauth/authenticate'
    access_token_url = 'https://api.twitter.com/oauth/access_token'
    user_info_url = (
        'https://api.twitter.com/1.1/account/verify_credentials.json?'
        'include_entities=true&include_email=true'
    )
    supports_jsonp = True

    @staticmethod
    def _x_user_parser(user, data):
        user.username = data.get('screen_name')
        user.id = data.get('id') or data.get('user_id')
        user.picture = data.get('profile_image_url')
        user.locale = data.get('lang')
        user.link = data.get('url')
        _location = data.get('location', '')
        if _location:
            user.location = _location.strip()
            _split_location = _location.split(',')
            if len(_split_location) > 1:
                _city, _country = _split_location
                user.country = _country.strip()
            else:
                _city = _split_location[0]
            user.city = _city.strip()
        return user


class Tumblr(OAuth1):
    """
    Tumblr |oauth1| provider.

    * Dashboard: http://www.tumblr.com/oauth/apps
    * Docs: http://www.tumblr.com/docs/en/api/v2#auth
    * API reference: http://www.tumblr.com/docs/en/api/v2

    Supported :class:`.User` properties:

    * id
    * name
    * username

    Unsupported :class:`.User` properties:

    * birth_date
    * city
    * country
    * email
    * gender
    * first_name
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

    supported_user_attributes = core.SupportedUserAttributes(
        id=True,
        name=True,
        username=True
    )

    request_token_url = 'http://www.tumblr.com/oauth/request_token'
    user_authorization_url = 'http://www.tumblr.com/oauth/authorize'
    access_token_url = 'http://www.tumblr.com/oauth/access_token'
    user_info_url = 'http://api.tumblr.com/v2/user/info'

    supports_jsonp = True

    @staticmethod
    def _x_user_parser(user, data):
        _user = data.get('response', {}).get('user', {})
        user.username = user.id = _user.get('name')
        return user


class UbuntuOne(OAuth1):
    """
    Ubuntu One |oauth1| provider.

    .. note::

        The UbuntuOne service
        `has been shut down <http://blog.canonical.com/2014/04/02/
        shutting-down-ubuntu-one-file-services/>`__.

    .. warning::

        Uses the `PLAINTEXT <http://oauth.net/core/1.0a/#anchor21>`_
        Signature method!

    * Dashboard: https://one.ubuntu.com/developer/account_admin/auth/web
    * Docs: https://one.ubuntu.com/developer/account_admin/auth/web
    * API reference: https://one.ubuntu.com/developer/contents

    """

    _signature_generator = PLAINTEXTSignatureGenerator

    request_token_url = 'https://one.ubuntu.com/oauth/request/'
    user_authorization_url = 'https://one.ubuntu.com/oauth/authorize/'
    access_token_url = 'https://one.ubuntu.com/oauth/access/'
    user_info_url = 'https://one.ubuntu.com/api/account/'


class Vimeo(OAuth1):
    """
    Vimeo |oauth1| provider.

    .. warning::

        Vimeo needs one more fetch to get rich user info!

    * Dashboard: https://developer.vimeo.com/apps
    * Docs: https://developer.vimeo.com/apis/advanced#oauth-endpoints
    * API reference: https://developer.vimeo.com/apis

    Supported :class:`.User` properties:

    * id
    * link
    * location
    * name
    * picture

    Unsupported :class:`.User` properties:

    * birth_date
    * city
    * country
    * email
    * gender
    * first_name
    * last_name
    * locale
    * nickname
    * phone
    * postal_code
    * timezone
    * username

    """

    supported_user_attributes = core.SupportedUserAttributes(
        id=True,
        link=True,
        location=True,
        name=True,
        picture=True
    )

    request_token_url = 'https://vimeo.com/oauth/request_token'
    user_authorization_url = 'https://vimeo.com/oauth/authorize'
    access_token_url = 'https://vimeo.com/oauth/access_token'
    user_info_url = ('http://vimeo.com/api/rest/v2?'
                     'format=json&method=vimeo.oauth.checkAccessToken')

    def _access_user_info(self):
        """
        Vimeo requires the user ID to access the user info endpoint, so we need
        to make two requests: one to get user ID and second to get user info.
        """
        response = super(Vimeo, self)._access_user_info()
        uid = response.data.get('oauth', {}).get('user', {}).get('id')
        if uid:
            return self.access('http://vimeo.com/api/v2/{0}/info.json'
                               .format(uid))
        return response

    @staticmethod
    def _x_user_parser(user, data):
        user.name = data.get('display_name')
        user.link = data.get('profile_url')
        user.picture = data.get('portrait_huge')
        return user


class Xero(OAuth1):
    """
    Xero |oauth1| provider.

    .. note::

        API returns XML!

    * Dashboard: https://api.xero.com/Application
    * Docs: http://blog.xero.com/developer/api-overview/public-applications/
    * API reference: http://blog.xero.com/developer/api/

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
    * location
    * nickname
    * phone
    * picture
    * postal_code
    * timezone
    * username

    """

    supported_user_attributes = core.SupportedUserAttributes(
        email=True,
        first_name=True,
        id=True,
        last_name=True,
        name=True
    )

    request_token_url = 'https://api.xero.com/oauth/RequestToken'
    user_authorization_url = 'https://api.xero.com/oauth/Authorize'
    access_token_url = 'https://api.xero.com/oauth/AccessToken'
    user_info_url = 'https://api.xero.com/api.xro/2.0/Users'

    @staticmethod
    def _x_user_parser(user, data):
        # Data is xml.etree.ElementTree.Element object.
        if not isinstance(data, dict):
            # But only on user.update()
            _user = data.find('Users/User')
            user.id = _user.find('UserID').text
            user.first_name = _user.find('FirstName').text
            user.last_name = _user.find('LastName').text
            user.email = _user.find('EmailAddress').text

        return user


class Yahoo(OAuth1):
    """
    Yahoo |oauth1| provider.

    * Dashboard: https://developer.apps.yahoo.com/dashboard/
    * Docs: http://developer.yahoo.com/oauth/guide/oauth-auth-flow.html
    * API: http://developer.yahoo.com/everything.html
    * API explorer: http://developer.yahoo.com/yql/console/

    Supported :class:`.User` properties:

    * city
    * country
    * id
    * link
    * location
    * name
    * nickname
    * picture

    Unsupported :class:`.User` properties:

    * birth_date
    * gender
    * locale
    * phone
    * postal_code
    * timezone
    * username

    """

    supported_user_attributes = core.SupportedUserAttributes(
        city=True,
        country=True,
        id=True,
        link=True,
        location=True,
        name=True,
        nickname=True,
        picture=True
    )

    request_token_url = 'https://api.login.yahoo.com/oauth/v2/' + \
                        'get_request_token'
    user_authorization_url = 'https://api.login.yahoo.com/oauth/v2/' + \
                             'request_auth'
    access_token_url = 'https://api.login.yahoo.com/oauth/v2/get_token'
    user_info_url = (
        'https://query.yahooapis.com/v1/yql?q=select%20*%20from%20'
        'social.profile%20where%20guid%3Dme%3B&format=json'
    )

    same_origin = False
    supports_jsonp = True

    @staticmethod
    def _x_user_parser(user, data):

        _user = data.get('query', {}).get('results', {}).get('profile', {})

        user.id = _user.get('guid')
        user.gender = _user.get('gender')
        user.nickname = _user.get('nickname')
        user.link = _user.get('profileUrl')

        emails = _user.get('emails')
        if isinstance(emails, list):
            for email in emails:
                if 'primary' in list(email.keys()):
                    user.email = email.get('handle')
        elif isinstance(emails, dict):
            user.email = emails.get('handle')

        user.picture = _user.get('image', {}).get('imageUrl')

        try:
            user.city, user.country = _user.get('location', ',').split(',')
            user.city = user.city.strip()
            user.country = user.country.strip()
        except ValueError:
            # probably user hasn't activated Yahoo Profile
            user.city = None
            user.country = None
        return user


class Xing(OAuth1):
    """
    Xing |oauth1| provider.

    * Dashboard: https://dev.xing.com/applications
    * Docs: https://dev.xing.com/docs/authentication
    * API reference: https://dev.xing.com/docs/resources

    Supported :class:`.User` properties:

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
    * location
    * name
    * phone
    * picture
    * postal_code
    * timezone
    * username

    Unsupported :class:`.User` properties:

    * nickname

    """

    request_token_url = 'https://api.xing.com/v1/request_token'
    user_authorization_url = 'https://api.xing.com/v1/authorize'
    access_token_url = 'https://api.xing.com/v1/access_token'
    user_info_url = 'https://api.xing.com/v1/users/me'

    supported_user_attributes = core.SupportedUserAttributes(
        birth_date=True,
        city=True,
        country=True,
        email=True,
        first_name=True,
        gender=True,
        id=True,
        last_name=True,
        link=True,
        locale=True,
        location=True,
        name=True,
        phone=True,
        picture=True,
        postal_code=True,
        timezone=True,
        username=True,
    )

    @staticmethod
    def _x_user_parser(user, data):
        _users = data.get('users', [])
        if _users and _users[0]:
            _user = _users[0]
            user.id = _user.get('id')
            user.name = _user.get('display_name')
            user.first_name = _user.get('first_name')
            user.last_name = _user.get('last_name')
            user.gender = _user.get('gender')
            user.timezone = _user.get('time_zone', {}).get('name')
            user.email = _user.get('active_email')
            user.link = _user.get('permalink')
            user.username = _user.get('page_name')
            user.picture = _user.get('photo_urls', {}).get('large')

            _address = _user.get('business_address', {})
            if _address:
                user.city = _address.get('city')
                user.country = _address.get('country')
                user.postal_code = _address.get('zip_code')
                user.phone = (
                    _address.get('phone', '')
                    or _address.get('mobile_phone', '')).replace('|', '')

            _languages = list(_user.get('languages', {}).keys())
            if _languages and _languages[0]:
                user.locale = _languages[0]

            _birth_date = _user.get('birth_date', {})
            _year = _birth_date.get('year')
            _month = _birth_date.get('month')
            _day = _birth_date.get('day')
            if _year and _month and _day:
                user.birth_date = datetime.datetime(_year, _month, _day)

        return user


# The provider type ID is generated from this list's indexes!
# Always append new providers at the end so that ids of existing providers
# don't change!
PROVIDER_ID_MAP = [
    Bitbucket,
    Flickr,
    Meetup,
    OAuth1,
    Plurk,
    Tumblr,
    Twitter,
    UbuntuOne,
    Vimeo,
    Xero,
    Xing,
    Yahoo,
]
