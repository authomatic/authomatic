# We need absolute iport to import from openid library which has the same name as this module
from __future__ import absolute_import
from openid.consumer import consumer
from openid.extensions import ax, pape, sreg
from simpleauth2 import providers
import simpleauth2
import logging

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
    
    def login(self, *args, **kwargs):
        
        super(OpenID, self).login(*args, **kwargs)
        
        # handle keyword arguments
        
        # realm
        use_realm = False if not kwargs.get('oi_use_realm') else True
        realm_body = kwargs.get('oi_realm_body') or ''
        realm_param = kwargs.get('oi_realm_param') or 'realm'
        xrds_param = kwargs.get('oi_xrds_param') or 'xrds'
        
        # sreg
        sreg_optional_fields = list(kwargs.get('oi_sreg') if kwargs.get('oi_sreg') is not None else self.SREG_FIELDS)
        sreg_required_fields = kwargs.get('oi_sreg_required') or []
        
        # ax
        ax_schemas = list(kwargs.get('oi_ax') if kwargs.get('oi_ax') is not None else self.AX_SCHEMAS)
        ax_required_schemas = list(kwargs.get('oi_ax_required') if kwargs.get('oi_ax_required') is not None else self.AX_SCHEMAS_REQUIRED)
        # add required schemas to schemas if not allready there
        for i in ax_required_schemas:
            if i not in ax_schemas:
                ax_schemas.append(i)
        
        # pape
        pape_policies = kwargs.get('oi_pape') if kwargs.get('oi_pape') is not None else self.PAPE_POLICIES
        
        
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
            auth_request = oi_consumer.begin(self.identifier)
            
            # add SREG extension
            # we need to remove required fields from optional fields because addExtension then raises an error
            sreg_optional_fields = [i for i in sreg_optional_fields if i not in sreg_required_fields]
            auth_request.addExtension(sreg.SRegRequest(optional=sreg_optional_fields, required=sreg_required_fields))
            
            # add AX extension
            ax_request = ax.FetchRequest()
            # set AX schemas
            for schema in ax_schemas:
                required = schema in ax_required_schemas
                ax_request.add(ax.AttrInfo(schema, required=required))
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
            
            self._reset_phase()
            
            # complete the authentication process
            response = oi_consumer.complete(self.adapter.get_request_params_dict(), self.uri)
            
            data = {}
            
            # on success
            if response.status == consumer.SUCCESS:
                
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
            
            #TODO: Handle errors
            if isinstance(response, consumer.FailureResponse):
                # error
                logging.info('ERROR ocured!')
                
            #TODO: move to self._finish()
            self.callback(simpleauth2.AuthEvent(self))
            


class Yahoo(OpenID):
    urls = ('me.yahoo.com', )

class Google(OpenID):
    urls = ('https://www.google.com/accounts/o8/id', )



