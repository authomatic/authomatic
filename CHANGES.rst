Version 0.0.8
-------------

* Added the ``supported_user_attributes`` to all provider classes.
* The :class:`.oauthh2.Facebook` provider now populates the ``user.city``
  and ``user.country`` properties.


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

