Config
------

.. seo-description::

    Config is a dictionary where you set up all the OAuth 1.0a, OAuth 2.0 and OpenID
    providers you want to use in your application.

The config is a dictionary listing all the **providers** you want to use in your app.
The keys are your internal **provider** names or slugs,
the values are dictionaries specifying configuration for a particular **provider** name.

Choose a provider implementation by assigning a |provider-class|_ to the ``"class_"`` key of
the nested *configuration dictionary*. All the other keys are just keyword arguments
which will be passed to the chosen |provider-class|_ constructor.

There is one special ``"__defaults__"`` key under which you can specify default
keyword arguments for all providers. Values of specific **providers** will override the default values.

.. note::

   In fact the config can be any object implementing a :func:`get` and :func:`values` method.
   If your app is running on |gae|_ you can use the :func:`.extras.gae.ndb_config`.


The **config** must have following structure:

::

   import authomatic

   CONFIG = {

       #===========================================================================
       # Defaults
       #===========================================================================

       '__defaults__': { # This is an optional special item where you can define default values for all providers.
            # You can override each default value by specifying it in concrete provider dict.
            'sreg': ['fullname', 'country'],
            'pape': ['http://schemas.openid.net/pape/policies/2007/06/multi-factor'],
       },

       #===========================================================================
       # OAuth 2.0
       #===========================================================================

       'facebook': { # Provider name.
            'class_': oauth2.Facebook,  # Provider class. Don't miss the trailing underscore!

            # Provider type specific keyword arguments:
            'short_name': 1, # Unique value used for serialization of credentials only needed by OAuth 2.0 and OAuth 1.0a.
            'consumer_key': '###################', # Key assigned to consumer by the provider.
            'consumer_secret': '###################', # Secret assigned to consumer by the provider.
            'scope': ['user_about_me', # List of requested permissions only needed by OAuth 2.0.
                      'email']
       },
       'google': {
            'class_': 'authomatic.providers.oauth2.Google', # Can be a fully qualified string path.

            # Provider type specific keyword arguments:
            'short_name': 2, # use authomatic.short_name() to generate this automatically
            'consumer_key': '###################',
            'consumer_secret': '###################',
            'scope': ['https://www.googleapis.com/auth/userinfo.profile',
                      'https://www.googleapis.com/auth/userinfo.email']
       },
       'windows_live': {
            'class_': 'oauth2.WindowsLive', # Can be a string path relative to the authomatic.providers module.

            # Provider type specific keyword arguments:
            'short_name': 3,
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
            'class_': oauth1.Twitter,

            # Provider type specific keyword arguments:
            'short_name': 4,
            'consumer_key': '###################',
            'consumer_secret': '###################'
            # OAuth 1.0a doesn't need scope.
       },

       #===========================================================================
       # OpenID
       #===========================================================================

       'oi': {
            'class_': openid.OpenID, # OpenID only needs this.
       },
       'gaeoi': {
            'class_': gaeopenid.GAEOpenID, # Google App Engine based OpenID provider.
       },
       'yahoo_oi': {
            'class_': openid.Yahoo, # OpenID provider with predefined identifier 'https://me.yahoo.com'.
            'sreg': ['email'] # This overrides the "sreg" defined in "__defaults__".
       },
       'google_oi': {
            'class_': openid.Google, # OpenID provider with predefined identifier 'https://www.google.com/accounts/o8/id'.
       }
   }
