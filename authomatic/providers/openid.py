# We need absolute iport to import from openid library which has the same name as this module
from __future__ import absolute_import
from openid.consumer import consumer
from openid.extensions import ax, pape, sreg
from authomatic import providers
from authomatic.exceptions import FailureError, CancellationError, OpenIDError
import datetime
import logging
import authomatic
from openid import oidutil


# supress openid logging to stderr
oidutil.log = lambda message, level=0: None


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


class OpenID(providers.AuthenticationProvider):
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
    
    @staticmethod
    def _user_parser(user, data):
        user.first_name = data.get('ax', {}).get('http://openid.net/schema/namePerson/first')
        user.last_name = data.get('ax', {}).get('http://openid.net/schema/namePerson/last')
        user.user_id = data.get('guid')
        user.link = data.get('ax', {}).get('http://openid.net/schema/contact/web/default')
        user.picture = data.get('ax', {}).get('http://openid.net/schema/media/image')
        user.nickname = data.get('sreg', {}).get('nickname')
        user.country = data.get('sreg', {}).get('country')
        user.postal_code = data.get('sreg', {}).get('postcode')
        
        user.name = data.get('sreg', {}).get('fullname') or \
            data.get('ax', {}).get('http://axschema.org/namePerson')
            
        user.gender = data.get('sreg', {}).get('gender') or \
            data.get('ax', {}).get('http://openid.net/schema/gender')
        
        user.locale = data.get('sreg', {}).get('language') or \
            data.get('ax', {}).get('http://openid.net/schema/language/pref')
        
        user.timezone = data.get('sreg', {}).get('timezone') or \
            data.get('ax', {}).get('http://openid.net/schema/timezone')
        
        user.email = data.get('sreg', {}).get('email') or \
            data.get('ax', {}).get('http://axschema.org/contact/email') or \
            data.get('ax', {}).get('http://schema.openid.net/contact/email')
        
        user.birth_date = datetime.datetime.strptime(data.get('sreg', {}).get('dob'), '%Y-%m-%d') if \
            data.get('sreg', {}).get('dob') else None
                
        return user
    
    
    @providers._login_decorator
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
        self.adapter.openid_store._log = self._log
        oi_consumer = consumer.Consumer(self.adapter.session, self.adapter.openid_store)        
        
        # handle realm and XRDS if there is only one query parameter
        if use_realm and len(self.adapter.params) == 1:
            realm_request = self.adapter.params.get(realm_param)
            xrds_request = self.adapter.params.get(xrds_param)                
        else:
            realm_request = None
            xrds_request = None
        
        # determine type of request
        if realm_request:
            #===================================================================
            # Realm HTML
            #===================================================================
            
            self._log(logging.INFO, 'Writing OpenID realm HTML to the response.')
            xrds_location = '{u}?{x}={x}'.format(u=self.adapter.url, x=xrds_param)
            self.adapter.write(REALM_HTML.format(xrds_location=xrds_location, body=realm_body))
            
        elif xrds_request:
            #===================================================================
            # XRDS XML
            #===================================================================
            
            self._log(logging.INFO, 'Writing XRDS XML document to the response.')
            self.adapter.set_header('Content-Type', 'application/xrds+xml')
            self.adapter.write(XRDS_XML.format(return_to=self.adapter.url))
        
        elif self.adapter.params.get('openid.mode'):
            #===================================================================
            # Phase 2 after redirect
            #===================================================================
            
            self._log(logging.INFO, 'Continuing OpenID authentication procedure after redirect.')
            
            # complete the authentication process
            response = oi_consumer.complete(self.adapter.params, self.adapter.url)            
            
            # on success
            if response.status == consumer.SUCCESS:
                
                data = {}
                
                # get user ID
                data['guid'] = response.getDisplayIdentifier()
                
                self._log(logging.INFO, 'Authentication successful.')
                
                # get user data from AX response
                ax_response = ax.FetchResponse.fromSuccessResponse(response)
                if ax_response and ax_response.data:
                    self._log(logging.INFO, 'Got AX data.')
                    ax_data = {}
                    # conver iterable values to their first item
                    for k, v in ax_response.data.iteritems():
                        if v and type(v) in (list, tuple):
                            ax_data[k] = v[0]
                    data['ax'] = ax_data
                
                
                # get user data from SREG response
                sreg_response = sreg.SRegResponse.fromSuccessResponse(response)
                if sreg_response and sreg_response.data:
                    self._log(logging.INFO, 'Got SREG data.')
                    data['sreg'] = sreg_response.data
                                
                
                # get data from PAPE response
                pape_response = pape.Response.fromSuccessResponse(response)
                if pape_response and pape_response.auth_policies:
                    self._log(logging.INFO, 'Got PAPE data.')
                    data['pape'] = pape_response.auth_policies
                
                # create user
                self._update_or_create_user(data)
                
                #===============================================================
                # We're done!
                #===============================================================
            
            elif response.status == consumer.CANCEL:
                raise CancellationError('User cancelled the verification of ID "{}"!'.format(response.getDisplayIdentifier()))
            
            elif response.status == consumer.FAILURE:
                raise FailureError(response.message)
            
        else:
            #===================================================================
            # Phase 1 before redirect
            #===================================================================
            
            self._log(logging.INFO, 'Starting OpenID authentication procedure.')
            
            # get AuthRequest object
            try:
                auth_request = oi_consumer.begin(self.identifier)
            except consumer.DiscoveryFailure as e:
                raise FailureError('Discovery failed for identifier {}!'.format(self.identifier),
                                   url=self.identifier,
                                   original_message=e.message)
            
            self._log(logging.INFO, 'Service discovery for identifier {} successfull.'.format(self.identifier))
            
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
            realm = return_to = '{u}?{r}={r}'.format(u=self.adapter.url, r=realm_param) if use_realm else self.adapter.url
                        
            url = auth_request.redirectURL(realm, return_to)
            
            if auth_request.shouldSendRedirect():
                # can be redirected
                url = auth_request.redirectURL(realm, return_to)
                self._log(logging.INFO, 'Redirecting user to {}.'.format(url))
                self.adapter.redirect(url)
            else:
                # must be sent as POST
                # this writes a html post form with auto-submit
                self._log(logging.INFO, 'Writing an auto-submit HTML form to the response.')
                form = auth_request.htmlMarkup(realm, return_to, False, dict(id='openid_form'))
                self.adapter.write(form)


class Yahoo(OpenID):
    identifier = 'me.yahoo.com'

class Google(OpenID):
    identifier = 'https://www.google.com/accounts/o8/id'


















    


