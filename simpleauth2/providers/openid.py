# We need absolute iport to import from openid library which has the same name as this module
from __future__ import absolute_import
from openid.consumer import consumer
from openid.extensions import ax, pape, sreg
from simpleauth2 import providers
from simpleauth2.exceptions import FailureError, DeniedError
import datetime
import logging
import simpleauth2

REALM_HTML = \
"""
<!DOCTYPE html>
<html>
    <head>
        <meta http-equiv="X-XRDS-Location" content="{xrds_location}" />
    </head>
    <body>{body}</body>
</html>
"""

XRDS_XML = \
"""
<?xml version="1.0" encoding="UTF-8"?>
<xrds:XRDS  
    xmlns:xrds="xri://$xrds"  
    xmlns:openid="http://openid.net/xmlns/1.0"  
    xmlns="xri://$xrd*($v*2.0)">  
    <XRD>  
        <Service priority="1">  
            <Type>http://specs.openid.net/auth/2.0/return_to</Type>  
            <URI>{return_to}</URI>  
        </Service>  
    </XRD>  
</xrds:XRDS>
"""


class _Session(object):
    """A dictionary like session as specified in openid.consumer.consumer.Consumer()"""
    
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


class OpenID(providers.OpenIDBaseProvider):
    """OpenID provider based on the python-openid library."""
        
    # http://openid.net/specs/openid-attribute-properties-list-1_0-01.html
    AX_SCHEMAS = ('http://axschema.org/contact/email',
                  'http://schema.openid.net/contact/email',
                  'http://axschema.org/namePerson',
                  'http://openid.net/schema/namePerson/first',
                  'http://openid.net/schema/namePerson/last',
                  'http://openid.net/schema/gender',
                  'http://openid.net/schema/language/pref',
                  'http://openid.net/schema/contact/web/default',
                  'http://openid.net/schema/media/image',
                  'http://openid.net/schema/timezone',)
    
    # google requires this schema
    AX_SCHEMAS_REQUIRED = ('http://schema.openid.net/contact/email', )
    
    # http://openid.net/specs/openid-simple-registration-extension-1_1-01.html#response_format
    SREG_FIELDS = ('nickname',
                 'email',
                 'fullname',
                 'dob',
                 'gender',
                 'postcode',
                 'country',
                 'language',
                 'timezone')
    
    # http://openid.net/specs/openid-provider-authentication-policy-extension-1_0.html#auth_policies
    PAPE_POLICIES = ['http://schemas.openid.net/pape/policies/2007/06/multi-factor-physical',
                     'http://schemas.openid.net/pape/policies/2007/06/multi-factor',
                     'http://schemas.openid.net/pape/policies/2007/06/phishing-resistant']
    
    # maps raw_user_info dict to User properties
    user_info_mapping = {
        'name':          lambda data:   data.get('sreg', {}).get('fullname') or \
                                        data.get('ax', {}).get('http://axschema.org/namePerson'),
                                        
        'first_name':    lambda data:   data.get('ax', {}).get('http://openid.net/schema/namePerson/first'),
        
        'last_name':     lambda data:   data.get('ax', {}).get('http://openid.net/schema/namePerson/last'),
        
        'user_id':       lambda data:   data.get('guid'),
        
        'gender':        lambda data:   data.get('sreg', {}).get('gender') or \
                                        data.get('ax', {}).get('http://openid.net/schema/gender'),
        
        'locale':        lambda data:   data.get('sreg', {}).get('language') or \
                                        data.get('ax', {}).get('http://openid.net/schema/language/pref'),
        
        'link':          lambda data:   data.get('ax', {}).get('http://openid.net/schema/contact/web/default'),
        
        'picture':       lambda data:   data.get('ax', {}).get('http://openid.net/schema/media/image'),
        
        'timezone':      lambda data:   data.get('sreg', {}).get('timezone') or \
                                        data.get('ax', {}).get('http://openid.net/schema/timezone'),
        
        'email':         lambda data:   data.get('sreg', {}).get('email') or \
                                        data.get('ax', {}).get('http://axschema.org/contact/email') or \
                                        data.get('ax', {}).get('http://schema.openid.net/contact/email'),
        
        'birth_date':    lambda data:   datetime.datetime.strptime(data.get('sreg', {}).get('dob'), '%Y-%m-%d') if \
                                        data.get('sreg', {}).get('dob') else None,
        
        'nickname':      lambda data:   data.get('sreg', {}).get('nickname'),
        
        'country':       lambda data:   data.get('sreg', {}).get('country'),
        
        'postal_code':   lambda data:   data.get('sreg', {}).get('postcode'),
    }
    
    @providers._error_decorator
    def login(self, *args, **kwargs):
        """
        Launches the OpenID authentication procedure.
        
        Accepts optional keyword arguments:
        
        oi_identifier
        
        oi_use_realm
        oi_realm_body
        oi_realm_param
        oi_xrds_param
        
        oi_sreg
        oi_sreg_required
        
        oi_ax
        oi_ax_required
        
        oi_pape
        """
        
        super(OpenID, self).login(*args, **kwargs)
        
        # handle keyword arguments
        
        # realm
        use_realm = kwargs.get('oi_use_realm', True)
        realm_body = kwargs.get('oi_realm_body', '')
        realm_param = kwargs.get('oi_realm_param', 'realm')
        xrds_param = kwargs.get('oi_xrds_param', 'xrds')
        
        # sreg
        sreg_optional_fields = list(kwargs.get('oi_sreg', self.SREG_FIELDS))
        sreg_required_fields = kwargs.get('oi_sreg_required', [])
        
        # ax
        ax_schemas = list(kwargs.get('oi_ax', self.AX_SCHEMAS))
        ax_required_schemas = list(kwargs.get('oi_ax_required', self.AX_SCHEMAS_REQUIRED))
        # add required schemas to schemas if not allready there
        for i in ax_required_schemas:
            if i not in ax_schemas:
                ax_schemas.append(i)
        
        # pape
        pape_policies = kwargs.get('oi_pape', self.PAPE_POLICIES)
                
        # Instantiate consumer
        oi_consumer = consumer.Consumer(_Session(self), self.adapter.get_openid_store())
                
        # handle realm
        if use_realm:
            
            if not self.identifier:
                
                if self.adapter.get_request_param(xrds_param):
                    # write XRDS XML if there is ?{xrds_param}={xrds_param} request parameter
                    self.adapter.set_response_header('Content-Type', 'application/xrds+xml')
                    self.adapter.write(XRDS_XML.format(return_to=self.uri))
                    
                elif self.adapter.get_request_param(realm_param) and len(self.adapter.get_request_params_dict()) == 1:
                    # write realm HTML but only if there is NOTHING BUT the ?{realm_param}={realm_param} request parameter
                    xrds_location = '{u}?{x}={x}'.format(u=self.uri, x=xrds_param)
                    self.adapter.write(REALM_HTML.format(xrds_location=xrds_location, body=realm_body))
        
        if self.phase == 0 and self.identifier:
            
            # get AuthRequest object
            try:
                auth_request = oi_consumer.begin(self.identifier)
            except consumer.DiscoveryFailure as e:
                raise FailureError(e.message)
            
            # add SREG extension
            # we need to remove required fields from optional fields because addExtension then raises an error
            sreg_optional_fields = [i for i in sreg_optional_fields if i not in sreg_required_fields]
            auth_request.addExtension(sreg.SRegRequest(optional=sreg_optional_fields, required=sreg_required_fields))
            
            # add AX extension
            ax_request = ax.FetchRequest()
            # set AX schemas
            for i in ax_schemas:
                required = i in ax_required_schemas
                ax_request.add(ax.AttrInfo(i, required=required))
            auth_request.addExtension(ax_request)
            
            # add PAPE extension
            auth_request.addExtension(pape.Request(pape_policies))           
            
            # prepare realm and return_to URLs
            realm = return_to = '{u}?{r}={r}'.format(u=self.uri, r=realm_param) if use_realm else self.uri
            
            if auth_request.shouldSendRedirect():
                # can be redirected
                url = auth_request.redirectURL(realm, return_to)
                self.adapter.redirect(url)
            else:
                # must be sent as POST
                # this writes a html post form with auto-submit
                form = auth_request.htmlMarkup(realm, return_to, False, dict(id='openid_form'))
                self.adapter.write(form)
            
            # finally move to next phase
            self._increase_phase()
                            
        
        elif self.phase == 1:
            
            # check whether the user has been redirected back by provider
            if not self.adapter.get_request_param('openid.mode'):
                raise DeniedError('User did not finish the redirect!')
            
            self._reset_phase()
                        
            # complete the authentication process
            response = oi_consumer.complete(self.adapter.get_request_params_dict(), self.uri)
            
            
            # on success
            if response.status == consumer.SUCCESS:
                
                data = {}
                
                # get user ID
                data['guid'] = response.getDisplayIdentifier()
                
                
                # get user data from AX response
                ax_response = ax.FetchResponse.fromSuccessResponse(response)
                if ax_response and ax_response.data:
                    ax_data = {}
                    # conver iterable values to their first item
                    for k, v in ax_response.data.iteritems():
                        if v and type(v) in (list, tuple):
                            ax_data[k] = v[0]
                    data['ax'] = ax_data
                
                
                # get user data from SREG response
                sreg_response = sreg.SRegResponse.fromSuccessResponse(response)
                if sreg_response and sreg_response.data:
                    data['sreg'] = sreg_response.data
                                
                
                # get data from PAPE response
                pape_response = pape.Response.fromSuccessResponse(response)
                if pape_response and pape_response.auth_policies:
                    data['pape'] = pape_response.auth_policies
                
                # create user
                self._update_or_create_user(data)
                
                self._finish()
            
            elif response.status == consumer.CANCEL:
                raise DeniedError('User cancelled the verification of ID "{}"!'.format(response.getDisplayIdentifier()))
            
            elif response.status == consumer.FAILURE:
                raise FailureError(response.message)


class Yahoo(OpenID):
    urls = ('me.yahoo.com', )

class Google(OpenID):
    urls = ('https://www.google.com/accounts/o8/id', )



