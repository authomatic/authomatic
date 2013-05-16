Providers
---------

.. contents::
   :backlinks: none

Providers are abstractions of the **provider** party of the
**provider**/**consumer**/**user** triangle and they are the very core of this library.
There is no reason for you to instantiate them manually.
You only should specify them in the :doc:`config` and access members of their instances
available in the :class:`.LoginResult` returned by the :func:`authomatic.login` function.

Some provider types accept additional keyword arguments in their constructor which you can pass to them
through the :func:`authomatic.login` function's keyword arguments or through the :doc:`config` like this:

.. note::

   Keyword arguments passed through :func:`authomatic.login` will override
   the values set in :doc:`config`.

::

    CONFIG = {
        'facebook': {
            'class_': oauth2.Facebook, # Subclass of AuthorizationProvider

            # AuthorizationProvider specific keyword arguments:
            'short_name': 1,
            'consumer_key': '###################',
            'consumer_secret': '###################',

            # oauth2.OAuth2 specific keyword arguments:
            'scope': ['user_about_me', 'email']
         },
         'openid': {
             'class_': openid.OpenID, # Subclass of AuthenticationProvider

             # AuthenticationProvider specific keyword arguments:
             'identifier_param': 'claimed_id',

             # openid.OpenID specific keyword arguments:
             'use_realm': True,
             'realm_body': 'OpenID Realm.',
             'realm_param': 'r',
             'xrds_param': 'x',
             'sreg': ['nickname', 'email'],
             'sreg_required': ['email'],
             'ax': ['http://axschema.org/contact/email', 'http://axschema.org/namePerson'],
             'ax_required': ['http://axschema.org/contact/email'],
             'pape': ['http://schemas.openid.net/pape/policies/2007/06/multi-factor']
        },  
    }


Additional keyword arguments by provider type:

+----------------------------------+---------------------------+-----------+-+
| Provider Type                    | Argument Name             | Required  | |
+==================================+===========================+===========+=+
| :class:`.OAuth2`                 | consumer_key              | yes       | |
+                                  +---------------------------+-----------+-+
|                                  | consumer_secret           | yes       | |
+                                  +---------------------------+-----------+-+
|                                  | short_name                | yes       | |
+                                  +---------------------------+-----------+-+
|                                  | scope                     |           | |
+                                  +---------------------------+-----------+-+
|                                  | offline                   |           | |
+                                  +---------------------------+-----------+-+
|                                  | user_authorization_params |           | |
+                                  +---------------------------+-----------+-+
|                                  | access_token_params       |           | |
+                                  +---------------------------+-----------+-+
|                                  | popup                     |           | |
+----------------------------------+---------------------------+-----------+-+
| :class:`.OAuth1`                 | consumer_key              | yes       | |
+                                  +---------------------------+-----------+-+
|                                  | consumer_secret           | yes       | |
+                                  +---------------------------+-----------+-+
|                                  | short_name                | yes       | |
+                                  +---------------------------+-----------+-+
|                                  | request_token_params      |           | |
+                                  +---------------------------+-----------+-+
|                                  | user_authorization_params |           | |
+                                  +---------------------------+-----------+-+
|                                  | access_token_params       |           | |
+                                  +---------------------------+-----------+-+
|                                  | popup                     |           | |
+----------------------------------+---------------------------+-----------+-+
| :class:`.OpenID`                 | identifier_param          |           | |
+                                  +---------------------------+-----------+-+
|                                  | use_realm                 |           | |
+                                  +---------------------------+-----------+-+
|                                  | realm_body                |           | |
+                                  +---------------------------+-----------+-+
|                                  | realm_param               |           | |
+                                  +---------------------------+-----------+-+
|                                  | xrds_param                |           | |
+                                  +---------------------------+-----------+-+
|                                  | sreg                      |           | |
+                                  +---------------------------+-----------+-+
|                                  | sreg_required             |           | |
+                                  +---------------------------+-----------+-+
|                                  | ax                        |           | |
+                                  +---------------------------+-----------+-+
|                                  | ax_required               |           | |
+                                  +---------------------------+-----------+-+
|                                  | pape                      |           | |
+                                  +---------------------------+-----------+-+
|                                  | popup                     |           | |
+----------------------------------+---------------------------+-----------+-+
| :class:`.GAEOpenID`              | identifier_param          |           | |
+                                  +---------------------------+-----------+-+
|                                  | popup                     |           | |
+----------------------------------+---------------------------+-----------+-+



Available provider classes:

+------------------------------+----------------------------+-------------------------------+-+
| |oauth2|                     | |oauth1|                   | |openid|                      | |
+==============================+============================+===============================+=+
| :class:`.oauth2.Behance`     | :class:`.oauth1.Bitbucket` | :class:`.openid.OpenID`       | |
+------------------------------+----------------------------+-------------------------------+-+
| :class:`.oauth2.Bitly`       |:class:`.oauth1.Flickr`     | :class:`.openid.Yahoo`        | |
+------------------------------+----------------------------+-------------------------------+-+
| :class:`.oauth2.Cosm`        |:class:`.oauth1.Meetup`     | :class:`.openid.Google`       | |
+------------------------------+----------------------------+-------------------------------+-+
| :class:`.oauth2.DeviantART`  | :class:`.oauth1.Plurk`     | :class:`.gaeopenid.GAEOpenID` | |
+------------------------------+----------------------------+-------------------------------+-+
| :class:`.oauth2.Facebook`    | :class:`.oauth1.Twitter`   | :class:`.gaeopenid.Yahoo`     | |
+------------------------------+----------------------------+-------------------------------+-+
| :class:`.oauth2.Foursquare`  | :class:`.oauth1.Tumblr`    | :class:`.gaeopenid.Google`    | |
+------------------------------+----------------------------+-------------------------------+-+
| :class:`.oauth2.GitHub`      | :class:`.oauth1.UbuntuOne` |                               | |
+------------------------------+----------------------------+-------------------------------+-+
| :class:`.oauth2.Google`      | :class:`.oauth1.Vimeo`     |                               | |
+------------------------------+----------------------------+-------------------------------+-+
| :class:`.oauth2.LinkedIn`    | :class:`.oauth1.Xero`      |                               | |
+------------------------------+----------------------------+-------------------------------+-+
| :class:`.oauth2.PayPal`      | :class:`.oauth1.Yahoo`     |                               | |
+------------------------------+----------------------------+-------------------------------+-+
| :class:`.oauth2.Reddit`      |                            |                               | |
+------------------------------+----------------------------+-------------------------------+-+
| :class:`.oauth2.Viadeo`      |                            |                               | |
+------------------------------+----------------------------+-------------------------------+-+
| :class:`.oauth2.VK`          |                            |                               | |
+------------------------------+----------------------------+-------------------------------+-+
| :class:`.oauth2.WindowsLive` |                            |                               | |
+------------------------------+----------------------------+-------------------------------+-+
| :class:`.oauth2.Yammer`      |                            |                               | |
+------------------------------+----------------------------+-------------------------------+-+
| :class:`.oauth2.Yandex`      |                            |                               | |
+------------------------------+----------------------------+-------------------------------+-+


.. automodule:: authomatic.providers.oauth2
   :members:

.. automodule:: authomatic.providers.oauth1
   :members:

.. automodule:: authomatic.providers.openid
   :members:

.. automodule:: authomatic.providers.gaeopenid
   :members:

.. automodule:: authomatic.providers
   :members:
