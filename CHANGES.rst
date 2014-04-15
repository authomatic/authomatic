Version 0.0.8
-------------

* Added the ``supported_user_attributes`` to all provider classes.
* The :class:`.oauthh2.Facebook` provider now populates the ``user.city``
  and ``user.country`` properties.
* The :class:`.oauthh2.Google` prowider now uses
  `https://www.googleapis.com/plus/v1/people/me` as the `user_info_url` instead of
  the deprecated `https://www.googleapis.com/oauth2/v3/userinfo`. Also the
  `user_info_scope` reflects these changes.
* Added missing :attr:`.oauthh2.DeviantART.user_info_scope`
* Changed the :attr:`.oauth1.Twitter.user_authorization_url` from
  `https://api.twitter.com/oauth/authorize` to
  `https://api.twitter.com/oauth/authenticate`.
* Added the :class:`oauth1.Xing` provider.
* Made compatible with **Python 2.6**.


Version 0.0.7
-------------

* Added user email extraction to :class:`.oauth1.Yahoo` provider.
* Added the ``access_headers`` and ``access_params``
  keyword arguments to the :class:`.AuthorizationProvider` constructor.
* Fixed a bug in :class:`.oauthh2.GitHub` provider when ``ValueError`` got risen
  when a user had only the city specified.
* Added a workaround for issue #11, failure of WebKit-based browsers to accept
  cookies set as part of a redirect response in some circumstances.


Version 0.0.6
-------------

* Added the :class:`.DjangoAdapter`.
* Switched the :attr:`.oauth2.Google.user_info_url` to Google API ``v3``.

