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
AX_SCHEMAS = ('http://axschema.org/contact/email',
              'http://schema.openid.net/contact/email',
              'http://axschema.org/namePerson',
              'http://openid.net/schema/namePerson/prefix',
              'http://openid.net/schema/namePerson/first',
              'http://openid.net/schema/namePerson/last',
              'http://openid.net/schema/namePerson/friendly')

SREG_FIELDS = ('nickname',
             'email',
             'fullname',
             'dob',
             'gender',
             'postcode',
             'country',
             'language',
             'timezone')

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
                for schema in AX_SCHEMAS:
                    # google needs this to be required
                    required = True if schema == 'http://schema.openid.net/contact/email' else False
                    ax_request.add(ax.AttrInfo(schema, required=required))
                
                auth_request.addExtension(ax_request)
                
                
                requested_policies = [pape.AUTH_MULTI_FACTOR,
                                      pape.AUTH_MULTI_FACTOR_PHYSICAL,
                                      pape.AUTH_PHISHING_RESISTANT]
                
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
            
            data = {}
            
            # on success
            if response.status == consumer.SUCCESS:
                
                # get id url
                data['guid'] = response.getDisplayIdentifier()
                
                
                # get user data from Attribute Exchange response
                ax_response = ax.FetchResponse.fromSuccessResponse(response)
                if ax_response:
                    data['ax'] = {}
                    for schema in AX_SCHEMAS:
                        # ax_response.get() throws a KeyError on non-existent key
                        try:
                            value = ax_response.get(schema)
                            # if vlaue is an iterable, replace it with the first item
                            if type(value) in (list, tuple):
                                value = value[0]
                            data['ax'][schema] = value
                        except KeyError:
                            pass
                
                
                # get user data from Simple Registration response
                sreg_response = sreg.SRegResponse.fromSuccessResponse(response)
                if sreg_response:
                    data['sreg'] = {}
                    for field in SREG_FIELDS:
                        value = sreg_response.get(field)
                        if value:
                            data['sreg'][field] = value
                                
                
                # get PAPE response
                pape_response = pape.Response.fromSuccessResponse(response)
                if pape_response and pape_response.auth_policies:
                    data['pape'] = pape_response.auth_policies
            
            
            self._update_or_create_user(data)
            
            
            if isinstance(response, consumer.FailureResponse):
                # error
                logging.info('ERROR ocured!')
                
            
            logging.info('IN PHASE 1')
            
            self.credentials = simpleauth2.Credentials(provider_type=self.get_type(),
                                                       short_name=self.short_name)
            
            self.callback(simpleauth2.AuthEvent(self, self.consumer, self.credentials))
            
            
class OpenID(_OpenIDBase):
    pass


class Yahoo(_OpenIDBase):
    urls = ('me.yahoo.com', )

class Google(_OpenIDBase):
    urls = ('https://www.google.com/accounts/o8/id', )



