# We need absolute iport to import from openid library which has the same name as this module
from __future__ import absolute_import
from openid.consumer import consumer
from openid.extensions import ax, pape, sreg
from simpleauth2 import providers
import simpleauth2
from urllib import urlencode
import logging
import re




PAPE_POLICIES = ['AUTH_PHISHING_RESISTANT',
                 'AUTH_MULTI_FACTOR',
                 'AUTH_MULTI_FACTOR_PHYSICAL',]

POLICY_PAIRS = [(p, getattr(pape, p)) for p in PAPE_POLICIES]

# http://openid.net/specs/openid-attribute-properties-list-1_0-01.html
AX_SCHEMAS = dict(email_ax='http://axschema.org/contact/email',
                  email_oi='http://schema.openid.net/contact/email',
                  name='http://axschema.org/namePerson',
                  name_prefix='http://openid.net/schema/namePerson/prefix',
                  first_name='http://openid.net/schema/namePerson/first',
                  last_name='http://openid.net/schema/namePerson/last',
                  middle_name='http://openid.net/schema/namePerson/middle',
                  name_suffix='http://openid.net/schema/namePerson/suffix',
                  name_friendly='http://openid.net/schema/namePerson/friendly',
                  guid='http://openid.net/schema/person/guid')

class _Session(object):
    def __init__(self, provider):
        self.provider = provider                            
    
    def __setitem__(self, key, value):
        self.provider.adapter.store_provider_data(self.provider.provider_name, key, value)
    
    def __getitem__(self, key):
        self.provider.adapter.retrieve_provider_data(self.provider.provider_name, key)
        
    def __delitem__(self, key):
        pass
    
    def get(self, key):
        self.provider.adapter.retrieve_provider_data(self.provider.provider_name, key)


class _OpenIDBase(providers.BaseProvider):
    
    @staticmethod
    def credentials_to_tuple(credentials):
        return ()
    
    @classmethod
    def credentials_from_tuple(cls, tuple_):
        return simpleauth2.Credentials(short_name=tuple_[0],
                                       provider_type=cls.get_type())    
    
    @classmethod
    def fetch_protected_resource(cls, adapter, url, credentials, content_parser, method='GET', response_parser=None):
        # return fake RPC
        
        dummy_result = lambda: None
        dummy_result.content = ''
        dummy_result.status_code = None
        dummy_result.headers = None
        
        dummy_rpc = lambda: None
        dummy_rpc.get_result = lambda: dummy_result
        
        return simpleauth2.RPC(dummy_rpc, response_parser, content_parser)
    
    
    def login(self):
        
        session = _Session(self)
        store = self.adapter.get_openid_store()
        
        cons = consumer.Consumer(session, store)
        
        if self.phase == 0:
            logging.info('IN PHASE 0')
            self._increase_phase()
            
            # get identifier
            identifier = self.urls[0] or self.adapter.get_request_param('id')
            
            
            
            if identifier:
                
                logging.info('Identifier is {}.'.format(identifier))
                
                # get AuthRequest object
                auth_request = cons.begin(identifier)
                
                # add Simple Registration extension
                auth_request.addExtension(sreg.SRegRequest(required=['dob'], optional=['email', 'nickname']))
                
                # add Attribute Exchange extension
                ax_request = ax.FetchRequest()
                
                # set AX schemas
                for v in AX_SCHEMAS.values():
                    # google needs this to be required
                    required = True if v == 'http://schema.openid.net/contact/email' else False
                    ax_request.add(ax.AttrInfo(v, required=required))
                
                auth_request.addExtension(ax_request)
                
                # add Add PAPE extension
                requested_policies = []
                
                # get requested policies from request
                policy_prefix = 'policy_'
                
                # loop through request params
                for k in self.adapter.get_request_params_dict().keys():
                    if k.startswith(policy_prefix):
                        # slice the rest after "policy_"
                        policy_attr = k[len(policy_prefix):]
                        if policy_attr in PAPE_POLICIES:
                            requested_policies.append(getattr(pape, policy_attr))
                
    #            requested_policies = [pape.AUTH_MULTI_FACTOR,
    #                                  pape.AUTH_MULTI_FACTOR_PHYSICAL,
    #                                  pape.AUTH_PHISHING_RESISTANT]
                
                logging.info('requested_policies = {}'.format(requested_policies))
                
                if requested_policies:
                    auth_request.addExtension(pape.Request(requested_policies))
                
                url = auth_request.redirectURL(self.uri, self.uri)
                
                logging.info('auth_request.shouldSendRedirect() = {}'.format(auth_request.shouldSendRedirect()))
                
    #            logging.info('auth_request.htmlMarkup() = {}'.format(auth_request.htmlMarkup(self.uri)))
                
                logging.info('auth_request.getMessage() = {}'.format(auth_request.getMessage(self.uri, self.uri)))
                
                if auth_request.shouldSendRedirect():
                    # redirect
                    self.adapter.redirect(url)
                else:
                    # send post request
                    pass
                
                self.adapter.redirect(url)
                
            else:
                logging.info('NO Identifier!')
                self._reset_phase()
            
        
        elif self.phase == 1:
            
            self._reset_phase()
            
            request_args = self.adapter.get_request_params_dict()
            response = cons.complete(request_args, self.uri)
            
            
            pape_response = None
            sreg_response = None
            ax_response = None
            user_data = {}
            
            # on success
            if response.status == consumer.SUCCESS:
                # get PAPE response
                pape_response = pape.Response.fromSuccessResponse(response)
                if not pape_response.auth_policies:
                    pape_response = None
                
                # get Simple Registration response
                sreg_response = sreg.SRegResponse.fromSuccessResponse(response)
                
                # get user data from Attribute Exchange response
                ax_response = ax.FetchResponse.fromSuccessResponse(response)
                if ax_response:
                    for k, v in AX_SCHEMAS.iteritems():
                        # ax_response.get() throws a KeyError on non-existent key
                        try:
                            user_data[k] = ax_response.get(v)
                        except KeyError:
                            pass
                else:
                    logging.info('NO AX RESPONSE!')
                
                user_data['id'] = response.getDisplayIdentifier()
                
                self.user = simpleauth2.User(raw_user_info=user_data,
                                             user_id=user_data.get('id'),
                                             username=user_data.get('name'),
                                             name=user_data.get('name'),
                                             email=user_data.get('email_ax') or user_data.get('email_oi'),)
            
            result = {consumer.CANCEL: 'Cancelled',
                      consumer.FAILURE: 'Failed',
                      consumer.SUCCESS: dict(url=response.getDisplayIdentifier(),
                                             sreg=sreg_response and sreg_response.items(),
                                             user_data=user_data,
                                             pape=pape_response)}
            
            logging.info('result[response.status] = {}'.format(result[response.status]))
            
            
            if isinstance(response, consumer.FailureResponse):
                # error
                logging.info('ERROR ocured!')
                
            
            logging.info('IN PHASE 1')
            
            self.credentials = simpleauth2.Credentials(provider_type=self.get_type(),
                                                       short_name=self.short_name)
            
            self.callback(simpleauth2.AuthEvent(self, self.consumer, self.user, self.credentials))
            
            
class OpenID(_OpenIDBase):
    pass


class Yahoo(_OpenIDBase):
    urls = ('me.yahoo.com', )

class Google(_OpenIDBase):
    urls = ('https://www.google.com/accounts/o8/id', )



