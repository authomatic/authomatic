Version 0.2.0
-------------

* Add :attr: email to :class: `oauth1.Twitter` provider.
* Added support for :attr:`.User.country` and :attr:`.User.city` to
  :class: `oauth1.Twitter` provider.
* Fix Twitter user info endpoint to include image url.
* Support passing of user state in oauth2 to support variable redirect urls.
* The :class:`.oauth2.Google` provider now uses
  ``https://www.googleapis.com/oauth2/v3/userinfo?alt=json`` as the ``user_info_url``
  instead of the deprecated ``https://www.googleapis.com/plus/v1/people/me``
* Added support for :attr:`email_verified` and :attr:`hosted_domain`
  to :class:`.oauth2.Google` provider.
* Removed support for :attr:`gender`, :attr:`link` and :attr:`birth_date`
  from :class:`.oauth2.Google` provider.
* Fix #160: Handle token_type of bearer (lower-case).
* Fix #130: explicitly request fields from Facebook.
* Adjusted naming of default scope for :class:`.oauth2.Facebook` to Facebook v2 API
* Added support for :attr:`.User.email` to the :class:`.oauth1.Bitbucket` provider.
* Added support for :attr:`.User.city`, updated :attr:`.User.country` and removed
  ::attr: `User.location` in the class:`.oauth2.LinkedIn` provider.

Version 0.1.0
-------------

* Introduced the :attr:`.User.access_token_response` attribute.
* Added support for :attr:`.User.email` and :attr:`.User.link` to the
  :class:`.oauth1.Plurk` provider.
* The :class:`.oauth1.Flickr` provider doesn't make the redundant API call
  during :meth:`.oauth1.Flickr.update_user` anymore.
* Removed support for :attr:`.User.birth_date` and :attr:`.User.gender`
  from the :class:`.oauth1.Yahoo` provider.
* Added the :attr:`.User.location` attribute.
* Removed support for :attr:`.User.country` and :attr:`.User.city` from
  :class:`.oauth1.Twitter` and :class:`.oauth2.GitHub` providers.
* Removed support for :attr:`.User.link` and :attr:`.User.picture` from
  :class:`.oauth1.Tumbler` provider.
* Removed support for :attr:`.User.username` and added support for
  :attr:`.User.birth_date` to :class:`.oauth2.Facebook` provider.
* :class:`.oauth2.Facebook` provider now uses ``v2`` api for user info request.
* Removed the ``r_fullprofile`` and ``r_fullprofile`` scopes from
  :attr:`.oauth2.LinkedIn.user_info_scope` due to the
  `Developer Program Transition <https://developer.linkedin.com/support/
  developer-program-transition>`__ and as a consequence removed support for
  :attr:`.User.birth_date` and :attr:`.User.phone`.

Version 0.0.13
--------------

* Removed logging of response body in the
  :meth:`.providers.AuthorizationProvider.access()` method.
* Fixed an error in :class:`.oauth2.Google` when the access token request
  resulted in an
  ``OAuth 2 parameters can only have a single value: client_secret`` error.

Version 0.0.12
--------------

* Fixed import errors of the **six** module.
* Fixed an bug when decoding binary provider response resulted in an error.
* Improved handling of ambiguous user location by some providers. Introduced
  the :class:`.User.location` attribute.

Version 0.0.11
--------------

* Added **Python 3.x** support thanks to
  `Emmanuel Leblond <https://github.com/touilleMan>`__.
* Fixed a bug when :class:`.authomatic.Response` could not be decoded.
* The :class:`.oauth2.Foursquare` provider now supports
  :attr:`.User.birth_date`.

Version 0.0.10
--------------

* Fixed a bug when saving non-JSON-serializable values to third party sessions
  by the ``python-openid`` package caused a ``KeyError``.
* Added the :class:`.oauth2.Eventbrite` provider.
* Added the :class:`.oauth2.Amazon` provider.
* Improved OAuth 2.0 Error Handling.

Version 0.0.9
-------------

* Updated *user info* URL scheme of the :class:`.oauth1.Yahoo` provider.
* The :class:`.oauth2.Yandex` provider now supports :attr:`.User.name` and.
  :attr:`.User.username` properties.
* Updated :class:`.oauth2.WindowsLive` |oauth2| endpoints.
* Fixed a bug with the :class:`.oauth2.Yammer` provider when *user info* request
  failed because the ``token_type`` was not ``"Bearer"``.
* The :class:`.oauth2.Yammer` provider now supports CSRF protection.
* Added the ``logger`` keyword argument to :class:`.Authomatic` constructor.
* Added the ``v=20140501`` parameter to each request of the
  :class:`.oauth2.Foursquare` provider.
* The :class:`.oauth2.LinkedIn` provider now supports the
  :attr:`.User.birth_date` attribute.
* The :class:`.oauth2.Reddit` provider now supports the
  :attr:`.User.username` attribute.

Version 0.0.8
-------------

* Added the ``supported_user_attributes`` to tested provider classes.
* The :class:`.oauth2.Facebook` provider now populates the :attr:`.User.city`
  and :attr:`.User.country` properties.
* The :class:`.oauth2.Google` prowider now uses
  ``https://www.googleapis.com/plus/v1/people/me`` as the ``user_info_url`` instead of
  the deprecated ``https://www.googleapis.com/oauth2/v3/userinfo``. Also the
  ``user_info_scope`` reflects these changes.
* Added missing ``user_info_scope`` to :class:`.oauth2.DeviantART` provider.
* Changed the ``user_authorization_url`` of :class:`.oauth1.Twitter` provider from
  ``https://api.twitter.com/oauth/authorize`` to
  ``https://api.twitter.com/oauth/authenticate``.
* Added the :class:`.oauth1.Xing` provider.
* Made compatible with **Python 2.6**.


Version 0.0.7
-------------

* Added user email extraction to :class:`.oauth1.Yahoo` provider.
* Added the ``access_headers`` and ``access_params``
  keyword arguments to the :class:`.AuthorizationProvider` constructor.
* Fixed a bug in :class:`.oauth2.GitHub` provider when ``ValueError`` got risen
  when a user had only the city specified.
* Added a workaround for
  `issue #11 <https://github.com/peterhudec/authomatic/issues/11>`__,
  when WebKit-based browsers failed to accept cookies set as part of a
  redirect response in some circumstances.

Version 0.0.6
-------------

* Added the :class:`.DjangoAdapter`.
* Switched the ``user_info_url`` attribute of the :class:`.oauth2.Google`
  provider to Google API ``v3``.

