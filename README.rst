==========
Authomatic
==========

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

Authomatic is an authorization/authentication client library for Python web applications
inspired by `Alex Vagin's <http://alex.cloudware.it/>`_ `Simpleauth <http://code.google.com/p/gae-simpleauth/>`_.
In fact I wanted to name it *Deathsimpleauth* but that would be too long.

Features
========

*	Loosely coupled.
*	Tiny but powerfull interface.
*	There is only one **optional** dependency, the |pyopenid|_ library.
*	Framework agnostic thanks to adapters.
*	Ready to accomodate future authorization/authentication protocols.
*	Makes calls to provider APIs a breeze.
*	JavaScript library as a bonus.
*	Out of the box support for:

	*	|oauth1|_ providers: **Bitbucket**, **Flickr**, **Meetup**, **Plurk**, **Twitter**,
		**Tumblr**, **UbuntuOne**, **Vimeo**, **Xero** and **Yahoo**.
	*	|oauth2|_ providers: **Behance**, **Bitly**, **Cosm**, **DeviantART**, **Facebook**,
		**Foursquare**, **GitHub**, **Google**, **LinkedIn**, **PayPal**, **Reddit**, **Viadeo**,
		**VK**, **WindowsLive**, **Yammer** and **Yandex**.
	*	|pyopenid|_ and |gae|_ based |openid|_.
	*	Mozilla Persona.

Usage
=====

Read the `exhaustive documentation <>`_.

Live Demo
=========

There is a live demo running on `http://authomatic-example.appspot.com`_.