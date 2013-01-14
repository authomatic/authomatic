from simpleauth2 import providers
from urllib import urlencode
import logging
import re
import simpleauth2


class OpenID(providers.BaseProvider):
    
    @staticmethod
    def _create_url(identity, callback):
        return 'abc'
    
    
    @staticmethod
    def _normalize_identifier(identifier):
        """
        Normalizes identifier according to http://openid.net/specs/openid-authentication-2_0.html#normalization_example
        """
        
        p = r'(\w+://)?([^/]+)(.*)'
        
        match = re.match(p, identifier)
        if match:
            scheme, domain, path = match.groups()
            if scheme:
                if scheme in ('http://', 'https://'):
                    scheme = scheme
                else:
                    raise simpleauth2.exceptions.OpenIDError('Invalid scheme "{}"! Valid values are "http://" and "https://".'.format(scheme))
            else:
                scheme = 'http://'
            path = path or '/'
            return ''.join((scheme, domain, path))
        
        else:
            raise simpleauth2.exceptions.OpenIDError('Bad identifier! Valid identifier must match this pattern: "(\w+://)?[^/]+.*".')
        
    
    def yadis_discovery(self, identifier):
        # replace lambda with XML parser
        response = self._fetch(lambda x: x, identifier,
                               headers={'Accept:': 'application/xrds+xml'})
        
        if response.headers.get('X-XRDS-Location'):
            xrds_location = response.headers.get('X-XRDS-Location')
            # fetch the location
            # limit crazy redirection
            self.yadis_discovery(xrds_location)
        else:
            # parse xml
            if response.headers.get('content-type') == 'application/xrds+xml':
                # parse XRDS
                pass
            else:
                # parse HTML
                # search for head.meta.http-equiv=X-XRDS-Location
                # fetch location
                pass
        
        
        
        logging.info('Open ID yadis = {}'.format(response.headers))
        return
    
    def _discover(self):
        pass
    
    def login(self):
        logging.info('Open ID provider = {}'.format(self.provider_name))
        
        url = self._create_url(self.urls[0], self.uri)
        
        
        
        if self.phase == 0:
            
            # get identifier
            identifier = self.urls[0] or self.adapter.get_request_param('id')
            
            # 1.) Normalize Open ID identifier http://openid.net/specs/openid-authentication-2_0.html#normalization
#            identifier = self._normalize_identifier(identifier)
#            
#            logging.info('Open ID identifier = {}'.format(identifier))
#            
#            self.yadis_discovery('https://www.google.com/accounts/o8/id')
            
            class Session(object):
                def __init__(self, provider):
                    self.provider = provider                            
                
                def __setitem__(self, key, value):
                    self.provider.adapter.store_provider_data(self.provider.provider_name, key, value)
                
                def __getitem__(self, key):
                    self.provider.adapter.retrieve_provider_data(self.provider.provider_name, key)
            
            session = Session(self.adapter)
            
#            consumer.Consumer(session, store, consumer_class)
            
            # 2.) Discover http://openid.net/specs/openid-authentication-2_0.html#discovery
            #
            # http://blog.astrumfutura.com/2007/02/yadis-service-discovery-for-identities-like-openid-part-1/
            #
            # should return
            #    provider endpoint URL
            #    protocol version
            # or
            #    claimed identifier
            #    provider local identifier
            # or
            #    XRDS document (xml)
            
            
            # 3.) Establish association http://openid.net/specs/openid-authentication-2_0.html#associations
            #
            #    fetch provider with parameters:
            #        common parameters:
            #            openid.ns
            #            openid.mode
            #            openid.assoc_type
            #                HMAC-SHA1
            #                HMAC-SHA256
            #            openid.session_type
            #                no-encryption
            #                DH-SHA1
            #                DH-SHA256
            #
            #        Diffie-Hellman Request Parameters:
            #            openid.dh_modulus
            #            openid.dh_gen
            #            openid.dh_consumer_public
            #
            #    on success returns
            #        common parameters:
            #            ns
            #            assoc_handle
            #            session_type
            #            assoc_type
            #            expires_in
            #
            #        Unencrypted Response Parameters:
            #            mac_key
            #
            #        Diffie-Hellman Response Parameters:
            #            dh_server_public
            #            enc_mac_key
            #
            #    on failure returns:
            #        ns
            #        error
            #        error_code
            #        session_type
            #        assoc_type
            
            
            # 4.) Request Authentication http://openid.net/specs/openid-authentication-2_0.html#requesting_authentication
            #
            #    redirect to provider with parameters:
            #        openid.ns
            #        openid.mode
            #            checkid_immediate
            #            checkid_setup
            #        openid.claimed_id
            #        openid.identity
            #        openid.assoc_handle
            #        openid.return_to
            #        openid.realm
            #
            #    on success returns:
            #        openid.ns
            #        openid.mode
            #        openid.op_endpoint
            #        openid.claimed_id
            #        openid.identity
            #        openid.return_to
            #        openid.response_nonce
            #        openid.invalidate_handle
            #        openid.assoc_handle
            #        openid.signed
            #        openid.sig
            #
            #    on failure returns:
            #        openid.ns
            #        openid.mode
                        
            
            pass
        
        elif self.phase == 1:
            
            # 5.) Verify assertion http://openid.net/specs/openid-authentication-2_0.html#verification
            #
            
            # Finally we get
            #
            #    openid.claimed_id (visible user id)
            #    
            
            pass

class Yahoo(OpenID):
    urls = ('me.yahoo.com', )