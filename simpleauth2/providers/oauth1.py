from simpleauth2 import providers
from urllib import urlencode
import binascii
import hashlib
import hmac
import logging
import simpleauth2
import time
import urllib


class OAuth1(providers.BaseProvider):
    def __init__(self, *args, **kwargs):
        super(OAuth1, self).__init__(*args, **kwargs)
        
        # create keys under which oauth token and secret will be stored in session
        self._oauth_token_key = self.provider_name + '_oauth_token'
        self._oauth_token_secret_key = self.provider_name + '_oauth_token_secret'
    
    def _update_credentials(self, response):
        
        credentials = super(OAuth1, self)._update_credentials(response)
        
        credentials.access_token = response.get('oauth_token')
        credentials.access_token_secret = response.get('oauth_token_secret')
        
        credentials.consumer_key = self.consumer.key
        credentials.consumer_secret = self.consumer.secret
        credentials.provider_type = self.get_type()
        
        return credentials    
    
    
    @staticmethod
    def create_url(url_type, base, consumer_key=None, consumer_secret=None, token=None, token_secret=None, verifier=None, method='GET', callback=None, nonce=None):
        """
        Creates a HMAC-SHA1 signed url to access OAuth 1.0 endpoint
        
        Taken from the oauth2 library
            
        1. Request Token URL http://oauth.net/core/1.0a/#auth_step1
            
            params:
               oauth_consumer_key
               
               oauth_callback (must be "oob" if not used with redirect)
               
               oauth_signature_method
               oauth_timestamp
               oauth_nonce
               oauth_version
               
               oauth_signature (we need consumer_secret to sign the request)
            
            returns:
               oauth_token
               oauth_token_secret
               oauth_callback_confirmed
        
        
        2. User Authorization URL http://oauth.net/core/1.0a/#auth_step2
        
            params:
               oauth_token
            
            redirects to provider which redirects to callback
            
            returns:
               oauth_token
               oauth_verifier
        
        
        3. Access Token URL http://oauth.net/core/1.0a/#auth_step3
            
            params:
                oauth_consumer_key
                oauth_token            
                oauth_verifier
                
                oauth_signature_method
                oauth_timestamp
                oauth_nonce
                oauth_version
                
                oauth_signature (we need consumer_secret to sign the request)
                
            returns:
                oauth_token
                oauth_token_secret
        
        
        4. Protected Resources URL http://oauth.net/core/1.0a/#anchor12
            
            params:
                oauth_consumer_key
                oauth_token
                
                oauth_signature_method
                oauth_timestamp
                oauth_nonce
                oauth_version
                
                oauth_signature (we need consumer_secret and token_secret to sign the request)
                
            returns:
                requested data    
        
        """
        
        params = {}
        
        if url_type == 1:
            # Request Token URL
            if consumer_key and consumer_secret and callback:
                params['oauth_consumer_key'] = consumer_key
                params['oauth_callback'] = callback
            else:
                raise simpleauth2.exceptions.OAuth1Error('Parameters consumer_key, consumer_secret and callback are required to create Request Token URL!')
            
        elif url_type == 2:
            # User Authorization URL
            if token:
                params['oauth_token'] = token
                return base + '?' + urlencode(params)
            else:
                raise simpleauth2.exceptions.OAuth1Error('Parameter token is required to create User Authorization URL!')
            
        elif url_type == 3:
            # Access Token URL
            if consumer_key and consumer_secret and token and verifier:
                params['oauth_token'] = token
                params['oauth_consumer_key'] = consumer_key
                params['oauth_verifier'] = verifier
            else:
                raise simpleauth2.exceptions.OAuth1Error('Parameters consumer_key, consumer_secret, token and verifier are required to create Access Token URL!')
            
        elif url_type == 4:
            # Protected Resources URL
            if consumer_key and consumer_secret and token and token_secret:
                params['oauth_token'] = token
                params['oauth_consumer_key'] = consumer_key
            else:
                raise simpleauth2.exceptions.OAuth1Error('Parameters consumer_key, consumer_secret, token and token_secret are required to create Protected Resources URL!')
        
        # Tign request.
        # Taken from the oauth2 library.
        
        params['oauth_signature_method'] = 'HMAC-SHA1'
        params['oauth_timestamp'] = str(int(time.time()))
        params['oauth_nonce'] = nonce
        params['oauth_version'] = '1.0'
        
        # prepare values for signing        
        # signed parameters must be sorted first by key, then by value
        params_to_sign = [(k, v) for k, v in params.items() if k != 'oauth_signature']
        params_to_sign.sort()
        params_to_sign = urllib.urlencode(params_to_sign)
        params_to_sign = params_to_sign.replace('+', '%20').replace('%7E', '~')
        
        key = '{}&'.format(simpleauth2.escape(consumer_secret))
        if token_secret:
            key += simpleauth2.escape(token_secret)
        
        raw = '&'.join((simpleauth2.escape(method),
                        simpleauth2.escape(base),
                        simpleauth2.escape(params_to_sign)))
        
        # sign with HMAC-SHA1 method
        hashed = hmac.new(key, raw, hashlib.sha1)
        
        params['oauth_signature'] = binascii.b2a_base64(hashed.digest())[:-1]
        
        return base + '?' + urlencode(params)
    
    def login(self):
        
        self._check_consumer()
        
        if self.phase == 0:
            
            self._increase_phase()
            
            parser = self._get_parser_by_index(0)
            
            # Create Request Token URL
            url1 = self.create_url(url_type=1,
                                     base=self.urls[0],
                                     consumer_key=self.consumer.key,
                                     consumer_secret=self.consumer.secret,
                                     callback=self.uri,
                                     nonce=self.adapter.generate_csrf())
            response = self._fetch(parser, url1)
            
            logging.info('RESPONSE = {}'.format(response.status_code))
            
            # check if response status is OK
            if response.status_code != 200:
                self.adapter.reset_phase(self.provider_name)
                raise Exception('Could not fetch a valid response from provider {}!'.format(self.provider_name))
            
            # extract OAuth token and save it to storage
            #oauth_token = parser(response).get('oauth_token')
            oauth_token = response.data.get('oauth_token')
            if not oauth_token:
                self.adapter.reset_phase(self.provider_name)
                raise Exception('Could not get a valid OAuth token from provider {}!'.format(self.provider_name))
            
            self.adapter.store_provider_data(self.provider_name, 'oauth_token', oauth_token)
            
            # extract OAuth token secret and save it to storage
            #oauth_token_secret = parser(response.setdefault('content'), {}).get('oauth_token_secret')
            oauth_token_secret = response.data.get('oauth_token_secret')
            if not oauth_token_secret:
                self.adapter.reset_phase(self.provider_name)
                raise Exception('Could not get a valid OAuth token secret from provider {}!'.format(self.provider_name))
            
            self.adapter.store_provider_data(self.provider_name, 'oauth_token_secret', oauth_token_secret)
            
            # Create User Authorization URL
            url2 = self.create_url(url_type=2,
                                     base=self.urls[1],
                                     token=oauth_token)
            self.adapter.redirect(url2)
        
        if self.phase == 1:
            
            # retrieve the OAuth token from session
            try:
                oauth_token = self.adapter.retrieve_provider_data(self.provider_name, 'oauth_token')
            except KeyError:
                self.adapter.reset_phase(self.provider_name)
                raise Exception('OAuth token could not be retrieved from storage!')
            
            try:
                oauth_token_secret = self.adapter.retrieve_provider_data(self.provider_name, 'oauth_token_secret')
            except KeyError:
                self.adapter.reset_phase(self.provider_name)
                raise Exception('OAuth token secret could not be retrieved from storage!')
            
            # extract the verifier
            verifier = self.adapter.get_request_param('oauth_verifier')
            if not verifier:
                self.adapter.reset_phase(self.provider_name)
                raise Exception('No OAuth verifier was returned by the {} provider!'.format(self.provider_name))
                        
            parser = self._get_parser_by_index(1)
            
            # Create Access Token URL
            url3 = self.create_url(url_type=3,
                                     base=self.urls[2],
                                     token=oauth_token,
                                     consumer_key=self.consumer.key,
                                     consumer_secret=self.consumer.secret,
                                     token_secret=oauth_token_secret,
                                     verifier=verifier,
                                     nonce=self.adapter.generate_csrf())
            
            response = self._fetch(parser, url3, method='POST')
            
            self._update_or_create_user(response.data)
            
            self.credentials = simpleauth2.Credentials(self.consumer.access_token, self.get_type(), self.short_name)
            self._update_credentials(response.data)
            
            # create event
            event = simpleauth2.AuthEvent(self, self.consumer, self.user, self.credentials)
            
            # reset phase
            self.adapter.reset_phase(self.provider_name)
            
            # call callback
            self.callback(event)


class Twitter(OAuth1):
    urls = ('https://api.twitter.com/oauth/request_token',
            'https://api.twitter.com/oauth/authorize',
            'https://api.twitter.com/oauth/access_token',
            'https://api.twitter.com/1/account/verify_credentials.json')
    
    parsers = (providers.QUERY_STRING_PARSER, providers.QUERY_STRING_PARSER)
    
    user_info_mapping = dict(user_id='short_name',
                            username='screen_name',
                            picture='profile_image_url',
                            locale='lang',
                            link='url')

