.. |gae| replace:: Google App Engine
.. _gae: https://developers.google.com/appengine/

.. |webapp2| replace:: Webapp2
.. _webapp2: http://webapp-improved.appspot.com/

.. |oauth2| replace:: OAuth 2.0
.. _oauth2: http://oauth.net/2/

.. |oauth1| replace:: OAuth 1.0a
.. _oauth1: http://oauth.net/core/1.0a/

.. |openid| replace:: OpenID
.. _openid: http://openid.net/

.. |pyopenid| replace:: python-openid
.. _pyopenid: http://pypi.python.org/pypi/python-openid/

==========
Authomatic
==========

 Google Summer of Code 2025:
  - Contributor: Andrew Himelstieb
  - Mentor: Jens Klein
    This package was included in the GSOC '25 program with the Plone Foundation. This 2.0 release was a major aspect to the project.

This 2.0 Release contains major breaking changes that will be incorperated into the official changelog soon.
These changes include the following: 
  - Removed Travis CI 
  - Removed Python Support for version < Python 3.10
  - Removed Support for Deprecated OAuth1 authentication Flow 
   - Includes all OAuth1 Provders:
    - Bitbucket
    - Flickr
    - Meetup
    - Plurk
    - Twitter
    - Tumblr
    - UbuntuOne
    - Vimeo
    - Xero
    - Xing
    - Yahoo
   - Removed OpenID support
   - The following Providers were updated to OAuth2 Authenication FLow and classes added to OAuth2.py:
    - Bitbucket
    - Twitter/x
    - Tumblr
    - Vimeo
    - Yahoo
  - New Functional Tests were created using pytest-httpx to mock the authentication flow in a ping-pong fashion for:
   - Google
   - Github
   - Facebook
   - Twitter/x
   - Amazon

**Authomatic**
is a **framework agnostic** library
for **Python** web applications
with a **minimalistic** but **powerful** interface
which simplifies **authentication** of users
by third party providers like **Facebook** or **Twitter**
through standards like **OAuth** and **OpenID**.

For more info visit the project page at http://authomatic.github.io/authomatic.

Maintainers
===========

**Authomatic** was migrated from a private project of Peter Hudec to a community-managed project.
Many thanks to Peter Hudec for all his hard work for creating and maintaining **authomatic**!
We are now a small team of volunteers, not paid for the work here.
Any help is appreciated!


Features
========

* Loosely coupled.
* Tiny but powerful interface.
* The |pyopenid|_ library is the only **optional** dependency.
* **Framework agnostic** thanks to adapters.
  Out of the box support for **Django**, **Flask**, **Pyramid** and **Webapp2**.
* Ready to accommodate future authorization/authentication protocols.
* Makes provider API calls a breeze.
* Asynchronous requests.
* JavaScript library as a bonus.
* Out of the box support for:

  * |oauth1|_ providers: **Bitbucket**, **Flickr**, **Meetup**, **Plurk**,
    **Twitter**, **Tumblr**, **UbuntuOne**, **Vimeo**, **Xero**, **Xing** and **Yahoo**.
  * |oauth2|_ providers: **Amazon**, **Behance**, **Bitly**, **Cosm**,
    **DeviantART**, **Eventbrite**, **Facebook**, **Foursquare**,
    **GitHub**, **Google**, **LinkedIn**, **PayPal**, **Reddit**,
    **Viadeo**, **VK**, **WindowsLive**, **Yammer** and **Yandex**.
  * |pyopenid|_ and |gae|_ based |openid|_.

License
=======

The package is licensed under
`MIT license <http://en.wikipedia.org/wiki/MIT_License>`__.

Requirements
============

Requires **Python 3.4** or newer.
**Python 3.x** support added in **Authomatic 0.0.11** thanks to Emmanuel Leblond <https://github.com/touilleMan>`__.

Live Demo
=========

There is a |gae| based live demo app running at
http://authomatic-example.appspot.com which makes use of most of the features.

Contribute
==========

Contributions of any kind are very welcome.
If you want to contribute, please read the
`Development Guide <http://authomatic.github.io/authomatic/development.html>`__
first. The project is hosted on
`GitHub <https://github.com/authomatic/authomatic>`__.

Usage
=====

Read the exhaustive documentation at http://authomatic.github.io/authomatic.

Changelog
=========

The `Changelog is part of the documentation <https://authomatic.github.io/authomatic/changelog.html>`_.

