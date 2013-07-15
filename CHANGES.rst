* Added user email extraction to :class:`.oauth1.Yahoo` provider.
* Added the ``access_headers`` and ``access_params``
  keyword arguments to the :class:`.AuthorizationProvider` constructor.
* Fixed a bug in :class:`.oauthh2.GitHub` provider when ``ValueError`` got risen
  when a user had only the city specified.