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
    Yahoo
    
"""

from authomatic import providers
from authomatic.exceptions import CancellationError, FailureError, OAuth1Error
from urllib import urlencode
import abc
import authomatic.core as core
import binascii
import datetime
import hashlib
import hmac
import logging
import time
import urllib
import urlparse


__all__ = ['OAuth1', 'Bitbucket', 'Flickr', 'Meetup', 'Plurk', 'Twitter', 'Tumblr', 'UbuntuOne',
           'Vimeo', 'Xero', 'Yahoo']


def _normalize_params(params):
    """
    Returns a normalized query string sorted first by key, then by value
    excluding the ``realm`` and ``oauth_signature`` parameters
    as specified here: http://oauth.net/core/1.0a/#rfc.section.9.1.1
    
    :param params:
        :class:`dict` or :class:`list` of tuples.
    """
    
    if type(params) == dict:
        params = params.items()
    
    # remove "realm" and "oauth_signature"
    params = [(k, v) for k, v in params if k not in ('oauth_signature', 'realm')]
    # sort
    params.sort()
    # convert to query string
    qs = urllib.urlencode(params)
    # replace "+" to "%20"
    qs = qs.replace('+', '%20')
    # replace "%7E" to "%20"
    qs = qs.replace('%7E', '~')
    
    return qs


def _join_by_ampersand(*args):
    return '&'.join([core.escape(i) for i in args])


def _create_base_string(method, base, params):
    """
    Returns base string for HMAC-SHA1 signature
    as specified in: http://oauth.net/core/1.0a/#rfc.section.9.1.3
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
    def create_signature(self, method, base, params, consumer_secret, token_secret=''):
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
            Access token secret as specified in http://oauth.net/core/1.0a/#anchor3.
        
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
        Returns a key for HMAC-SHA1 signature
        as specified at: http://oauth.net/core/1.0a/#rfc.section.9.2
        
        :param str consumer_secret:
            :attr:`.core.Consumer.secret`
            
        :param str token_secret:
            Access token secret as specified in http://oauth.net/core/1.0a/#anchor3.
        
        :returns:
            Key to sign the request with.
        """
        
        return _join_by_ampersand(consumer_secret, token_secret or '')
    
    
    @classmethod
    def create_signature(cls, method, base, params, consumer_secret, token_secret=''):
        """
        Returns HMAC-SHA1 signature
        as specified at: http://oauth.net/core/1.0a/#rfc.section.9.2
        
        :param str method:
            HTTP method of the request to be signed.
            
        :param str base:
            Base URL of the request without query string an fragment.
            
        :param dict params:
            Dictionary or list of tuples of the request parameters.
            
        :param str consumer_secret:
            :attr:`.core.Consumer.secret`
            
        :param str token_secret:
            Access token secret as specified in http://oauth.net/core/1.0a/#anchor3.
        
        :returns:
            The signature string.
        """
        
        base_string = _create_base_string(method, base, params)
        key = cls._create_key(consumer_secret, token_secret)
        
        hashed = hmac.new(key, base_string, hashlib.sha1)
        
        
        base64_encoded = binascii.b2a_base64(hashed.digest())[:-1]
        
        return base64_encoded


class PLAINTEXTSignatureGenerator(BaseSignatureGenerator):
    """
    PLAINTEXT signature generator.
    See: http://oauth.net/core/1.0a/#anchor21
    """
    
    method = 'PLAINTEXT'
    
    @classmethod
    def create_signature(cls, method, base, params, consumer_secret, token_secret=''):
        
        consumer_secret = urllib.quote(consumer_secret, '')
        token_secret = urllib.quote(token_secret, '')
        
        return urllib.quote('&'.join((consumer_secret, token_secret)), '')


class OAuth1(providers.AuthorisationProvider):
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
            The *key* assigned to our application (**consumer**) by the **provider**.
            
        :param str consumer_secret:
            The *secret* assigned to our application (**consumer**) by the **provider**.
            
        :param id:
            A unique short name used to serialize :class:`.Credentials`.
            
        :param dict user_authorisation_params:
            A dictionary of additional request parameters for **user authorisation request**.
            
        :param dict access_token_params:
            A dictionary of additional request parameters for **access token request**.
            
        :param dict request_token_params:
            A dictionary of additional request parameters for **request token request**.
        """
        
        super(OAuth1, self).__init__(*args, **kwargs)
        
        self.request_token_params = self._kwarg(kwargs, 'request_token_params', {})
    
    
    #===========================================================================
    # Abstract properties
    #===========================================================================
    
    @abc.abstractproperty
    def request_token_url(self):
        """
        :class:`str` URL where we can get the |oauth1| request token.
        see http://oauth.net/core/1.0a/#auth_step1.
        """
    
    
    #===========================================================================
    # Internal methods
    #===========================================================================
    
    @classmethod
    def create_request_elements(cls, request_type, credentials, url, params=None, headers=None,
                                 method='GET', verifier='', callback=''):
        """
        Creates |oauth1| request elements.
        """
        
        logging.info('CRE: params = {}'.format(params))
        params = params or {}
        logging.info('CRE: params = {}'.format(params))
        headers = headers or {}
        
        consumer_key = credentials.consumer_key or ''
        consumer_secret = credentials.consumer_secret or ''
        token = credentials.token or ''
        token_secret = credentials.token_secret or ''
        
        # separate url base and query parameters
        url, base_params = cls._split_url(url)
        
        # add extracted params to future params
        params.update(dict(base_params))
        
        if request_type == cls.USER_AUTHORISATION_REQUEST_TYPE:
            # no need for signature
            if token:
                params['oauth_token'] = token
            else:
                raise OAuth1Error('Credentials with valid token are required to create User Authorization URL!')
        else:
            # signature needed
            if request_type == cls.REQUEST_TOKEN_REQUEST_TYPE:
                # Request Token URL
                if consumer_key and consumer_secret and callback:
                    params['oauth_consumer_key'] = consumer_key
                    params['oauth_callback'] = callback
                else:
                    raise OAuth1Error('Credentials with valid consumer_key, consumer_secret and ' +\
                                                             'callback are required to create Request Token URL!')
                
            elif request_type == cls.ACCESS_TOKEN_REQUEST_TYPE:
                # Access Token URL
                if consumer_key and consumer_secret and token and verifier:
                    params['oauth_token'] = token
                    params['oauth_consumer_key'] = consumer_key
                    params['oauth_verifier'] = verifier
                else:
                    raise OAuth1Error('Credentials with valid consumer_key, consumer_secret, token ' +\
                                                             'and argument verifier are required to create Access Token URL!')
                
            elif request_type == cls.PROTECTED_RESOURCE_REQUEST_TYPE:
                # Protected Resources URL
                if consumer_key and consumer_secret and token and token_secret:
                    params['oauth_token'] = token
                    params['oauth_consumer_key'] = consumer_key
                else:
                    raise OAuth1Error('Credentials with valid consumer_key, consumer_secret, token and ' +\
                                                             'token_secret are required to create Protected Resources URL!')
            
            # Sign request.
            # http://oauth.net/core/1.0a/#anchor13
            
            # Prepare parameters for signature base string
            # http://oauth.net/core/1.0a/#rfc.section.9.1
            params['oauth_signature_method'] = cls._signature_generator.method
            params['oauth_timestamp'] = str(int(time.time()))
            params['oauth_nonce'] = cls.csrf_generator()
            params['oauth_version'] = '1.0'
            
            logging.info('CRE: params = {}'.format(params))
            # add signature to params
            params['oauth_signature'] = cls._signature_generator.create_signature(method, url, params, consumer_secret, token_secret)
            logging.info('CRE: params = {}'.format(params))
        
        params = urlencode(params)
        
        body = None
        
        if method in ('POST', 'PUT'):
            body = params
        else:
            url = url + '?' + params
        
        return url, body, method, headers
    
    
    #===========================================================================
    # Exposed methods
    #===========================================================================
    
    
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
        denied = core.middleware.params.get('denied')
        verifier = core.middleware.params.get('oauth_verifier', '')
        request_token = core.middleware.params.get('oauth_token', '')
        
        if request_token and verifier:
            # Phase 2 after redirect with success
            self._log(logging.INFO, 'Continuing OAuth 1.0a authorisation procedure after redirect.')
            token_secret = self._session_get('token_secret')
            if not token_secret:
                raise FailureError('Unable to retrieve token secret from storage!')
            
            # Get Access Token          
            self._log(logging.INFO, 'Fetching for access token from {}.'.format(self.access_token_url))
            
            self.credentials.token = request_token
            self.credentials.token_secret = token_secret
            
            request_elements = self.create_request_elements(request_type=self.ACCESS_TOKEN_REQUEST_TYPE,
                                                             url=self.access_token_url,
                                                             credentials=self.credentials,
                                                             verifier=verifier,
                                                             params=self.access_token_params)
            
            response = self._fetch(*request_elements)
            
            if response.status != 200:
                raise FailureError('Failed to obtain OAuth 1.0a  oauth_token from {}! HTTP status code: {}.'\
                                   .format(self.access_token_url, response.status),
                                   original_message=response.content,
                                   status=response.status,
                                   url=self.access_token_url)
            
            self._log(logging.INFO, 'Got access token.')
            
            self.credentials.token = response.data.get('oauth_token', '')
            self.credentials.token_secret = response.data.get('oauth_token_secret', '')
            
            self.credentials = self._x_credentials_parser(self.credentials, response.data)
            
            self._update_or_create_user(response.data, self.credentials)
            
            #===================================================================
            # We're done!
            #===================================================================
            
        elif denied:
            # Phase 2 after redirect denied
            raise CancellationError('User denied the request token {} during a redirect to {}!'.\
                                  format(denied, self.user_authorisation_url),
                                  original_message=denied,
                                  url=self.user_authorisation_url)
        else:
            # Phase 1 before redirect
            self._log(logging.INFO, 'Starting OAuth 1.0a authorisation procedure.')
            
            # Fetch for request token
            request_elements = self.create_request_elements(request_type=self.REQUEST_TOKEN_REQUEST_TYPE,
                                                             credentials=self.credentials,
                                                             url=self.request_token_url,
                                                             callback=core.middleware.url,
                                                             params=self.request_token_params)
            
            self._log(logging.INFO, 'Fetching for request token and token secret.')
            response = self._fetch(*request_elements)
            
            # check if response status is OK
            if response.status != 200:
                raise FailureError('Failed to obtain request token from {}! HTTP status code: {} content: {}'\
                                  .format(self.request_token_url, response.status, response.content),
                                  original_message=response.content,
                                  status=response.status,
                                  url=self.request_token_url)
            
            # extract request token
            request_token = response.data.get('oauth_token')
            if not request_token:
                raise FailureError('Response from {} doesn\'t contain oauth_token parameter!'.format(self.request_token_url),
                                  original_message=response.content,
                                  url=self.request_token_url)
            
            # we need request token for user authorisation redirect
            self.credentials.token = request_token
                        
            # extract token secret and save it to storage
            token_secret = response.data.get('oauth_token_secret')
            if token_secret:
                # we need token secret after user authorisation redirect to get access token
                self._session_set('token_secret', token_secret)
            else:
                raise FailureError('Failed to obtain token secret from {}!'.format(self.request_token_url),
                                  original_message=response.content,
                                  url=self.request_token_url)
            
            
            self._log(logging.INFO, 'Got request token and token secret')
            
            # Create User Authorization URL
            request_elements = self.create_request_elements(request_type=self.USER_AUTHORISATION_REQUEST_TYPE,
                                                             credentials=self.credentials,
                                                             url=self.user_authorisation_url,
                                                             params=self.user_authorisation_params)
            
            self._log(logging.INFO, 'Redirecting user to {}.'.format(request_elements[0]))
            
            core.middleware.redirect(request_elements[0])


class Bitbucket(OAuth1):
    """
    Bitbucket |oauth1| provider.
    
    * Dashboard: https://bitbucket.org/account/user/peterhudec/api
    * Docs: https://confluence.atlassian.com/display/BITBUCKET/oauth+Endpoint
    * API reference: https://confluence.atlassian.com/display/BITBUCKET/Using+the+Bitbucket+REST+APIs
    """
    
    request_token_url = 'https://bitbucket.org/!api/1.0/oauth/request_token'
    user_authorisation_url = 'https://bitbucket.org/!api/1.0/oauth/authenticate'
    access_token_url = 'https://bitbucket.org/!api/1.0/oauth/access_token'
    user_info_url = 'https://api.bitbucket.org/1.0/user'
    
    @staticmethod
    def _x_user_parser(user, data):
        _user = data.get('user', {})
        user.username = user.id = _user.get('username')
        user.name = _user.get('display_name')
        user.first_name = _user.get('first_name')
        user.last_name = _user.get('last_name')
        user.picture = _user.get('avatar')
        user.link = _user.get('resource_uri')
        return user


class Flickr(OAuth1):
    """
    Flickr |oauth1| provider.
    
    * Dashboard: https://www.flickr.com/services/apps/
    * Docs: https://www.flickr.com/services/api/auth.oauth.html
    * API reference: https://www.flickr.com/services/api/
    """
    
    request_token_url = 'http://www.flickr.com/services/oauth/request_token'
    user_authorisation_url = 'http://www.flickr.com/services/oauth/authorize'
    access_token_url = 'http://www.flickr.com/services/oauth/access_token'
    user_info_url = 'http://api.flickr.com/services/rest?method=flickr.test.login&format=json&nojsoncallback=1'
    
    
    @staticmethod
    def _x_user_parser(user, data):
        
        _user = data.get('user', {})
        
        user.name = data.get('fullname') or _user.get('username', {}).get('_content')
        user.id = data.get('user_nsid') or _user.get('id')
        
        return user


class Meetup(OAuth1):
    """
    Meetup |oauth1| provider.
    
    .. note::
        
        Meetup also supports |oauth2| but you need the **user ID** to update the **user** info,
        which they don't provide in the |oauth2| access token response.
    
    * Dashboard: http://www.meetup.com/meetup_api/oauth_consumers/
    * Docs: http://www.meetup.com/meetup_api/auth/#oauth
    * API: http://www.meetup.com/meetup_api/docs/
    """
    
    request_token_url = 'https://api.meetup.com/oauth/request/'
    user_authorisation_url = 'http://www.meetup.com/authorize/'
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
    """
    
    request_token_url = 'http://www.plurk.com/OAuth/request_token'
    user_authorisation_url = 'http://www.plurk.com/OAuth/authorize'
    access_token_url = 'http://www.plurk.com/OAuth/access_token'
    user_info_url = 'http://www.plurk.com/APP/Profile/getOwnProfile'
    
    
    @staticmethod
    def _x_user_parser(user, data):
        
        _user = data.get('user_info', {})
        
        user.locale = _user.get('default_lang')
        user.username = _user.get('display_name')
        user.id = _user.get('id') or _user.get('uid')
        user.nickname = _user.get('nick_name')
        user.name = _user.get('full_name')
        user.gender = _user.get('gender')
        user.timezone = _user.get('timezone')
        user.picture = 'http://avatars.plurk.com/{}-big2.jpg'.format(user.id)
        
        user.city, user.country = _user.get('location', ',').split(',')
        user.city = user.city.strip()
        user.country = user.country.strip()
        
        try:
            user.birth_date = datetime.datetime.strptime(_user.get('date_of_birth'), "%a, %d %b %Y %H:%M:%S %Z")
        except:
            user.birth_date = data.get('date_of_birth')
        
        return user


class Twitter(OAuth1):
    """
    Twitter |oauth1| provider.
    
    * Dashboard: https://dev.twitter.com/apps
    * Docs: https://dev.twitter.com/docs
    * API reference: https://dev.twitter.com/docs/api
    """
    
    request_token_url = 'https://api.twitter.com/oauth/request_token'
    user_authorisation_url = 'https://api.twitter.com/oauth/authorize'
    access_token_url = 'https://api.twitter.com/oauth/access_token'
    user_info_url = 'https://api.twitter.com/1/account/verify_credentials.json'
        
    @staticmethod
    def _x_user_parser(user, data):
        user.username = data.get('screen_name')
        user.picture = 'http://api.twitter.com/1/users/profile_image?screen_name={}&size=original'.format(data.get('screen_name'))
        user.locale = data.get('lang')
        user.link = data.get('url')
        return user


class Tumblr(OAuth1):
    """
    Tumblr |oauth1| provider.
    
    * Dashboard: http://www.tumblr.com/oauth/apps
    * Docs: http://www.tumblr.com/docs/en/api/v2#auth
    * API reference: http://www.tumblr.com/docs/en/api/v2
    """
    
    request_token_url = 'http://www.tumblr.com/oauth/request_token'
    user_authorisation_url = 'http://www.tumblr.com/oauth/authorize'
    access_token_url = 'http://www.tumblr.com/oauth/access_token'
    user_info_url = 'http://api.tumblr.com/v2/user/info'
    
    
    @staticmethod
    def _x_user_parser(user, data):
        _user = data.get('response', {}).get('user', {})
        
        user.username = user.id = _user.get('name')
        user.link = _user.get('blogs', [{}])[0].get('url')
        
        if user.link:
            _host = urlparse.urlsplit(user.link).netloc
            user.picture = 'http://api.tumblr.com/v2/blog/{}/avatar/512'.format(_host)
        
        return user


class UbuntuOne(OAuth1):
    """
    Ubuntu One |oauth1| provider.
    
    .. warning::
        
        Uses the `PLAINTEXT <http://oauth.net/core/1.0a/#anchor21>`_ Signature method!
    
    * Dashboard: https://one.ubuntu.com/developer/account_admin/auth/web
    * Docs: https://one.ubuntu.com/developer/account_admin/auth/web
    * API reference: https://one.ubuntu.com/developer/contents
    """
    
    _signature_generator = PLAINTEXTSignatureGenerator
    
    request_token_url = 'https://one.ubuntu.com/oauth/request/'
    user_authorisation_url = 'https://one.ubuntu.com/oauth/authorize/'
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
    """
    
    request_token_url = 'https://vimeo.com/oauth/request_token'
    user_authorisation_url = 'https://vimeo.com/oauth/authorize'
    access_token_url = 'https://vimeo.com/oauth/access_token'
    user_info_url = 'http://vimeo.com/api/rest/v2?format=json&method=vimeo.oauth.checkAccessToken'
    
    
    @staticmethod
    def _x_user_parser(user, data):
        
        _user = data.get('oauth', {}).get('user', {})
        user.name = _user.get('display_name')
        user.id = _user.get('id')
        user.username = _user.get('username')
        
        # Vimeo needs user ID to get rich info so we need to make one more fetch.
        if user.id:
            response = user.provider.access('http://vimeo.com/api/v2/{}/info.json'.format(user.username))
            if response and response.status == 200:
                user.name = response.data.get('display_name')
                user.city, user.country = response.data.get('location', ',').split(',')
                user.city = user.city.strip()
                user.country = user.country.strip()
                user.link = response.data.get('profile_url')
                user.picture = response.data.get('portrait_huge')
        
        return user


class Xero(OAuth1):
    """
    Xero |oauth1| provider.
    
    .. note::
        
        API returns XML!
    
    * Dashboard: https://api.xero.com/Application
    * Docs: http://blog.xero.com/developer/api-overview/public-applications/
    * API reference: http://blog.xero.com/developer/api/
    """
    
    request_token_url = 'https://api.xero.com/oauth/RequestToken'
    user_authorisation_url = 'https://api.xero.com/oauth/Authorize'
    access_token_url = 'https://api.xero.com/oauth/AccessToken'
    user_info_url = 'https://api.xero.com/api.xro/2.0/Users'
    
    
    @staticmethod
    def _x_user_parser(user, data):
        # Data is xml.etree.ElementTree.Element object.
        if type(data) is not dict:
            # But only on user.update()
            
            _user = data.find('Users/User')
            
            user.id = _user.find('UserID').text
            user.first_name = _user.find('FirstName').text
            user.last_name = _user.find('LastName').text
        
        return user


class Yahoo(OAuth1):
    """
    Yahoo |oauth1| provider.
    
    * Dashboard: https://developer.apps.yahoo.com/dashboard/
    * Docs: http://developer.yahoo.com/oauth/guide/oauth-auth-flow.html
    * API: http://developer.yahoo.com/everything.html
    * API explorer: http://developer.yahoo.com/yql/console/
    """
    
    request_token_url = 'https://api.login.yahoo.com/oauth/v2/get_request_token'
    user_authorisation_url = 'https://api.login.yahoo.com/oauth/v2/request_auth'
    access_token_url = 'https://api.login.yahoo.com/oauth/v2/get_token'
    user_info_url = 'http://query.yahooapis.com/v1/yql?q=select%20*%20from%20social.profile%20where%20guid%3Dme&format=json'
    
#    same_origin = False
    same_origin = True
    
    @staticmethod
    def _x_user_parser(user, data):
        
        _user = data.get('query', {}).get('results', {}).get('profile', {})
        
        user.id = _user.get('guid')
        user.gender = _user.get('gender')
        user.nickname = _user.get('nickname')
        user.link = _user.get('profileUrl')
        
        user.picture = _user.get('image', {}).get('imageUrl')
        
        user.city, user.country = _user.get('location', ',').split(',')
        user.city = user.city.strip()
        user.country = user.country.strip()
        
        _date = _user.get('birthdate')
        _year = _user.get('birthYear')
        
        if _date and _year:
            _full = _date + '/' + _year
            try:
                user.birth_date = datetime.datetime.strptime(_full, "%m/%d/%Y")
            except:
                user.birth_date = _full
        
        return user


# The provider type ID is generated from this list's indexes!
# Allways apppend new providers at the end so that ids of existing providers dont change!
PROVIDER_ID_MAP = [OAuth1, Bitbucket, Flickr, Meetup, Plurk, Twitter, Tumblr, UbuntuOne, Vimeo, Xero, Yahoo]






