Config
------

The **config** is a dictionary of dictionaries where you specify
which providers you want to use and how are they configured.
It should be passed to the :doc:`adapter's <adapters>` constructor.

.. note::
   
   :doc:`adapters` can provide other means of config creation.
   The :class:`authomatic.adapters.gaewebapp2.GAEWebapp2Adapter` for instance
   provides a NDB datamodel as a default config.

The **config** must have following structure:

::

   import authomatic
   
   PROVIDERS = {
   
       #===========================================================================
       # OAutht 2.0
       #===========================================================================
       
       'facebook': { # Provider name.
            'short_name': 1, # Unique value used for serialization of credentials only needed by OAuth 2.0 and OAuth 1.0a.
            'class_name': oauth2.Facebook,  # Provider class
            'consumer_key': '###################', # Key assigned to consumer by the provider.
            'consumer_secret': '###################', # Secret assigned to consumer by the provider.
            'scope': ['user_about_me', # List of requested permissions only needed by OAuth 2.0.
                      'email']
       },
       'google': {
            'short_name': 2, # use authomatic.short_name() to generate this automatically
            'class_name': 'authomatic.providers.oauth2.Google', # Can be a fully qualified string path.
            'consumer_key': '###################',
            'consumer_secret': '###################',
            'scope': ['https://www.googleapis.com/auth/userinfo.profile',
                      'https://www.googleapis.com/auth/userinfo.email']
       },
       'windows_live': {
            'short_name': 3,
            'class_name': 'oauth2.WindowsLive', # Can be a string path relative to the authomatic.providers module.
            'consumer_key': '###################',
            'consumer_secret': '###################',
            'scope': ['wl.basic',
                      'wl.emails',
                      'wl.photos']
       },
       
       #===========================================================================
       # OAuth 1.0a
       #===========================================================================
       
       'twitter': {
            'short_name': 4,
            'class_name': oauth1.Twitter,
            'consumer_key': '###################',
            'consumer_secret': '###################'
            # OAuth 1.0a doesn't need scope.
       },
                
       #===========================================================================
       # OpenID
       #===========================================================================
       
       'oi': {
            'class_name': openid.OpenID, # OpenID only needs this.
       },             
       'gaeoi': {
            'class_name': gaeopenid.GAEOpenID, # Google App Engine based OpenID provider.
       },             
       'google_oi': {
            'class_name': openid.Yahoo, # OpenID provider with predefined identifier 'https://me.yahoo.com'.
       },             
       'yahoo_oi': {
            'class_name': openid.Google, # OpenID provider with predefined identifier 'https://www.google.com/accounts/o8/id'.
       }
   }
