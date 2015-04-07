Version 0.0.12
--------------

* Fixed import errors of the **six** module.
* Fixed an bug when decoding binary provider response resulted in an error.

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

.. note::

    This version is still in development and has not been released to
    `PyPI <https://pypi.python.org/pypi/Authomatic>`__ yet.

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

