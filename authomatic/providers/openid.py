# -*- coding: utf-8 -*-
"""
|openid| Providers
----------------------------------

Providers which implement the |openid|_ protocol based on the
`python-openid`_ library.

.. warning::

    This providers are dependent on the |pyopenid|_ package.
    
.. autosummary::
    
    OpenID
    Yahoo
    Google 

"""

# We need absolute import to import from openid library which has the same name as this module
from __future__ import absolute_import
import datetime
import logging
import time

from openid import oidutil
from openid.consumer import consumer
from openid.extensions import ax, pape, sreg
from openid.association import Association

from authomatic import providers
from authomatic.exceptions import FailureError, CancellationError, OpenIDError


__all__ = ['OpenID', 'Yahoo', 'Google']


# Suppress openid logging.
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


class SessionOpenIDStore(object):
    """
    A very primitive session-based implementation of the :class:`openid.store.interface.OpenIDStore`
    interface of the `python-openid`_ library.
    
    .. warning::
        
        Nonces get verified only by their timeout. Use on your own risk!

    """
    
    _log = lambda level, message: None
    
    def __init__(self, session, nonce_timeout=None):
        """
        :param int nonce_timeout:
            Nonces older than this in seconds will be considered expired.
            Default is 600.
        """
        
        self.session = session
        self.nonce_timeout = nonce_timeout or 600
    
    def storeAssociation(self, server_url, association):
        self._log(logging.DEBUG, 'SessionOpenIDStore: Storing association to session.')
        # Always store only one association as a tuple.
        self.session['oia'] = (server_url, association.handle, association.serialize())
    
    
    def getAssociation(self, server_url, handle=None):
        # Try to get association.
        assoc = self.session.get('oia')
        
        if assoc and assoc[0] == server_url:
            # If found deserialize and return it.
            self._log(logging.DEBUG, 'SessionOpenIDStore: Association found.')
            return Association.deserialize(assoc[2])
        else:
            self._log(logging.DEBUG, 'SessionOpenIDStore: Association not found.')
    
    
    def removeAssociation(self, server_url, handle):
        # Just inform the caller that it's gone.
        True
    
    
    def useNonce(self, server_url, timestamp, salt):
        # Evaluate expired nonces as false.
        age = int(time.time()) - int(timestamp)
        if age < self.nonce_timeout:
            return True
        else:
            self._log(logging.ERROR, 'SessionOpenIDStore: Expired nonce!')
            return False


class OpenID(providers.AuthenticationProvider):
    """
    |openid|_ provider based on the `python-openid`_ library.    
    """
    
    AX = ['http://axschema.org/contact/email',
          'http://schema.openid.net/contact/email',
          'http://axschema.org/namePerson',
          'http://openid.net/schema/namePerson/first',
          'http://openid.net/schema/namePerson/last',
          'http://openid.net/schema/gender',
          'http://openid.net/schema/language/pref',
          'http://openid.net/schema/contact/web/default',
          'http://openid.net/schema/media/image',
          'http://openid.net/schema/timezone']
    
    AX_REQUIRED = ['http://schema.openid.net/contact/email']
    
    SREG = ['nickname',
            'email',
            'fullname',
            'dob',
            'gender',
            'postcode',
            'country',
            'language',
            'timezone']
    
    PAPE = ['http://schemas.openid.net/pape/policies/2007/06/multi-factor-physical',
            'http://schemas.openid.net/pape/policies/2007/06/multi-factor',
            'http://schemas.openid.net/pape/policies/2007/06/phishing-resistant']
    
    def __init__(self, *args, **kwargs):
        """
        Accepts additional keyword arguments:
        
        :param store:
            Any object which implements :class:`openid.store.interface.OpenIDStore`
            of the `python-openid`_ library.
        
        :param bool use_realm:
            Whether to use `OpenID realm <http://openid.net/specs/openid-authentication-2_0-12.html#realms>`_.
            If ``True`` the realm HTML document will be accessible at
            ``{current url}?{realm_param}={realm_param}``
            e.g. ``http://example.com/path?realm=realm``.
        
        :param str realm_body:
            Contents of the HTML body tag of the realm.
        
        :param str realm_param:
            Name of the query parameter to be used to serve the realm.
        
        :param str xrds_param:
            The name of the query parameter to be used to serve the
            `XRDS document <http://openid.net/specs/openid-authentication-2_0-12.html#XRDS_Sample>`_.
        
        :param list sreg:
            List of strings of optional
            `SREG <http://openid.net/specs/openid-simple-registration-extension-1_0.html>`_ fields.
            Default = :attr:`OpenID.SREG`.
                
        :param list sreg_required:
            List of strings of required
            `SREG <http://openid.net/specs/openid-simple-registration-extension-1_0.html>`_ fields.
            Default = ``[]``.        
        
        :param list ax:
            List of strings of optional
            `AX <http://openid.net/specs/openid-attribute-exchange-1_0.html>`_ schemas.
            Default = :attr:`OpenID.AX`.
        
        :param list ax_required:
            List of strings of required
            `AX <http://openid.net/specs/openid-attribute-exchange-1_0.html>`_ schemas.
            Default = :attr:`OpenID.AX_REQUIRED`.
                
        :param list pape:
            of requested
            `PAPE <http://openid.net/specs/openid-provider-authentication-policy-extension-1_0.html>`_
            policies.
            Default = :attr:`OpenID.PAPE`.
        
        As well as those inherited from :class:`.AuthenticationProvider` constructor.
        """
        
        super(OpenID, self).__init__(*args, **kwargs)
        
        # Allow for other openid store implementations.
        self.store = self._kwarg(kwargs, 'store', SessionOpenIDStore(self.session))
        
        # Realm
        self.use_realm = self._kwarg(kwargs, 'use_realm', True)
        self.realm_body = self._kwarg(kwargs, 'realm_body', '')
        self.realm_param = self._kwarg(kwargs, 'realm_param', 'realm')
        self.xrds_param = self._kwarg(kwargs, 'xrds_param', 'xrds')        
        
        #SREG
        self.sreg = self._kwarg(kwargs, 'sreg', self.SREG)
        self.sreg_required = self._kwarg(kwargs, 'sreg_required', [])
        
        # AX
        self.ax = self._kwarg(kwargs, 'ax', self.AX)
        self.ax_required = self._kwarg(kwargs, 'ax_required', self.AX_REQUIRED)
        # add required schemas to schemas if not already there
        for i in self.ax_required:
            if i not in self.ax:
                self.ax.append(i)
        
        # PAPE
        self.pape = self._kwarg(kwargs, 'pape', self.PAPE)
    
    
    @staticmethod
    def _x_user_parser(user, data):
        
        user.first_name = data.get('ax', {}).get('http://openid.net/schema/namePerson/first')
        user.last_name = data.get('ax', {}).get('http://openid.net/schema/namePerson/last')
        user.id = data.get('guid')
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
                
        # Instantiate consumer
        self.store._log = self._log
        oi_consumer = consumer.Consumer(self.session, self.store)
        
        # handle realm and XRDS if there is only one query parameter
        if self.use_realm and len(self.params) == 1:
            realm_request = self.params.get(self.realm_param)
            xrds_request = self.params.get(self.xrds_param)                
        else:
            realm_request = None
            xrds_request = None
        
        # determine type of request
        if realm_request:
            #===================================================================
            # Realm HTML
            #===================================================================
            
            self._log(logging.INFO, 'Writing OpenID realm HTML to the response.')
            xrds_location = '{u}?{x}={x}'.format(u=self.url, x=self.xrds_param)
            self.write(REALM_HTML.format(xrds_location=xrds_location, body=self.realm_body))
            
        elif xrds_request:
            #===================================================================
            # XRDS XML
            #===================================================================
            
            self._log(logging.INFO, 'Writing XRDS XML document to the response.')
            self.set_header('Content-Type', 'application/xrds+xml')
            self.write(XRDS_XML.format(return_to=self.url))
        
        elif self.params.get('openid.mode'):
            #===================================================================
            # Phase 2 after redirect
            #===================================================================
            
            self._log(logging.INFO, 'Continuing OpenID authentication procedure after redirect.')
            
            # complete the authentication process
            response = oi_consumer.complete(self.params, self.url)            
            
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
                    # convert iterable values to their first item
                    for k, v in ax_response.data.items():
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
                raise CancellationError('User cancelled the verification of ID "{0}"!'.format(response.getDisplayIdentifier()))
            
            elif response.status == consumer.FAILURE:
                raise FailureError(response.message)
            
        elif self.identifier:  # As set in AuthenticationProvider.__init__
            #===================================================================
            # Phase 1 before redirect
            #===================================================================
            
            self._log(logging.INFO, 'Starting OpenID authentication procedure.')
            
            # get AuthRequest object
            try:
                auth_request = oi_consumer.begin(self.identifier)
            except consumer.DiscoveryFailure as e:
                raise FailureError('Discovery failed for identifier {0}!'.format(self.identifier),
                                   url=self.identifier,
                                   original_message=e.message)
            
            self._log(logging.INFO, 'Service discovery for identifier {0} successful.'.format(self.identifier))
            
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
                realm = return_to = '{u}?{r}={r}'.format(u=self.url, r=self.realm_param)
            else:
                realm = return_to = self.url
                        
            url = auth_request.redirectURL(realm, return_to)
            
            if auth_request.shouldSendRedirect():
                # can be redirected
                url = auth_request.redirectURL(realm, return_to)
                self._log(logging.INFO, 'Redirecting user to {0}.'.format(url))
                self.redirect(url)
            else:
                # must be sent as POST
                # this writes a html post form with auto-submit
                self._log(logging.INFO, 'Writing an auto-submit HTML form to the response.')
                form = auth_request.htmlMarkup(realm, return_to, False, dict(id='openid_form'))
                self.write(form)
        else:
            raise OpenIDError('No identifier specified!')



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


















    


