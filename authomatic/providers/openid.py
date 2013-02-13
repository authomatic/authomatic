"""
OpenID Providers
----------------------------------

Providers compatible with the |openid|_ protocol based on the
`python-openid`_ library.

.. warning::
    
    These providers are more expensive than the :mod:`.gaeopenid` providers.
    The login procedure requires **one more fetch** and up to **8 DB accesses**!

.. autosummary::
    
    OpenID
    Yahoo
    Google 

"""

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

__all__ = ['OpenID', 'Yahoo', 'Google']

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
    """
    |openid|_ provider based on the `python-openid`_ library.
    
    .. automethod:: __init__
    
    """
        
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
    
    def __init__(self, *args, **kwargs):
        """
        Accepts optional keyword arguments:
        :attr:`.identifier`,
        :attr:`.use_realm`,
        :attr:`.realm_body`,
        :attr:`.realm_param`,
        :attr:`.xrds_param`,
        :attr:`.sreg`,
        :attr:`.sreg_required`,
        :attr:`.ax`,
        :attr:`.ax_required`,
        :attr:`.pape`.
        """
        
        super(OpenID, self).__init__(*args, **kwargs)
        
        
        #=======================================================================
        # Realm
        #=======================================================================
        
        #: Whether to use `OpenID realm <http://openid.net/specs/openid-authentication-2_0-12.html#realms>`_.
        #: If ``True`` the realm HTML document will be accessible at
        #: ``{current url}?{realm_param}={realm_param}``
        #: e.g. ``http://example.com/path?realm=realm``.
        self.use_realm = self._kwarg(kwargs, 'use_realm', True)
#        self.use_realm = kwargs.get('use_realm', True)
        
        #: The contents of the HTML body tag of the realm.
        self.realm_body = self._kwarg(kwargs, 'realm_body', '')
#        self.realm_body = kwargs.get('realm_body', '')
        
        #: The name of the query parameter to be used to serve the realm.
        self.realm_param = self._kwarg(kwargs, 'realm_param', 'realm')
#        self.realm_param = kwargs.get('realm_param', 'realm')
        
        #: The name of the query parameter to be used to serve the
        #: `XRDS document <http://openid.net/specs/openid-authentication-2_0-12.html#XRDS_Sample>`_.
        self.xrds_param = self._kwarg(kwargs, 'xrds_param', 'xrds')
#        self.xrds_param = kwargs.get('xrds_param', 'xrds')
        
        
        #=======================================================================
        # SREG
        #=======================================================================
        
        #: :class:`list` of optional
        #: `SREG <http://openid.net/specs/openid-simple-registration-extension-1_0.html>`_ fields.
        self.sreg = self._kwarg(kwargs, 'sreg', self.SREG_FIELDS)
#        self.sreg = list(kwargs.get('sreg', self.SREG_FIELDS))
        
        #: :class:`list` of required
        #: `SREG <http://openid.net/specs/openid-simple-registration-extension-1_0.html>`_ fields.
        self.sreg_required = self._kwarg(kwargs, 'sreg_required', [])
#        self.sreg_required = kwargs.get('sreg_required', [])
        
        
        #=======================================================================
        # AX
        #=======================================================================
        
        #: :class:`list` of optional
        #: `AX <http://openid.net/specs/openid-attribute-exchange-1_0.html>`_ schemas.
        self.ax = self._kwarg(kwargs, 'ax', self.AX_SCHEMAS)
#        self.ax = list(kwargs.get('ax', self.AX_SCHEMAS))
        
        #: :class:`list` of required
        #: `AX <http://openid.net/specs/openid-attribute-exchange-1_0.html>`_ schemas.
        self.ax_required = self._kwarg(kwargs, 'ax_required', self.AX_SCHEMAS_REQUIRED)
#        self.ax_required = list(kwargs.get('ax_required', self.AX_SCHEMAS_REQUIRED))
        
        # add required schemas to schemas if not allready there
        for i in self.ax_required:
            if i not in self.ax:
                self.ax.append(i)
        
        
        #=======================================================================
        # PAPE
        #=======================================================================
        
        #: :class:`list` of requested
        #: `PAPE <http://openid.net/specs/openid-provider-authentication-policy-extension-1_0.html>`_
        #: policies.
        self.pape = self._kwarg(kwargs, 'pape', self.PAPE_POLICIES)
#        self.pape = kwargs.get('pape', self.PAPE_POLICIES)
    
    
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
    
    
    @providers.login_decorator
    def login(self):
        """Launches the OpenID authentication procedure."""
        
                
        # Instantiate consumer
        self.adapter.openid_store._log = self._log
        oi_consumer = consumer.Consumer(self.adapter.session, self.adapter.openid_store)        
        
        # handle realm and XRDS if there is only one query parameter
        if self.use_realm and len(self.adapter.params) == 1:
            realm_request = self.adapter.params.get(self.realm_param)
            xrds_request = self.adapter.params.get(self.xrds_param)                
        else:
            realm_request = None
            xrds_request = None
        
        # determine type of request
        if realm_request:
            #===================================================================
            # Realm HTML
            #===================================================================
            
            self._log(logging.INFO, 'Writing OpenID realm HTML to the response.')
            xrds_location = '{u}?{x}={x}'.format(u=self.adapter.url, x=self.xrds_param)
            self.adapter.write(REALM_HTML.format(xrds_location=xrds_location, body=self.realm_body))
            
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
            self.sreg = [i for i in self.sreg if i not in self.sreg_required]
            auth_request.addExtension(sreg.SRegRequest(optional=self.sreg,
                                                       required=self.sreg_required))
            
            # add AX extension
            ax_request = ax.FetchRequest()
            # set AX schemas
            for i in self.ax:
                required = i in self.ax_required
                ax_request.add(ax.AttrInfo(i, required=required))
            auth_request.addExtension(ax_request)
            
            # add PAPE extension
            auth_request.addExtension(pape.Request(self.pape))           
            
            # prepare realm and return_to URLs
            if self.use_realm:
                realm = return_to = '{u}?{r}={r}'.format(u=self.adapter.url, r=self.realm_param)
            else:
                realm = return_to = self.adapter.url
            
#            realm = return_to = '{u}?{r}={r}'.format(u=self.adapter.url, r=self.realm_param) if self.use_realm else self.adapter.url
                        
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
    """
    Yahoo  :class:`.OpenID` provider with the :attr:`.identifier` predefined to ``"me.yahoo.com"``.
    """
    
    identifier = 'me.yahoo.com'

class Google(OpenID):
    """
    Google :class:`.OpenID` provider with the :attr:`.identifier` predefined to ``"https://www.google.com/accounts/o8/id"``.
    """
    
    identifier = 'https://www.google.com/accounts/o8/id'


















    


