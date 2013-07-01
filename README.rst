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

Authomatic
is an **authorization/authentication**
client library for Python web applications
inspired by Alex Vagin’s `Simpleauth <http://code.google.com/p/gae-simpleauth/>`_.
In fact, I almost named it *Deadsimpleauth*,
but that name would be too long
for a succinct library.

For more info visit the project page at http://peterhudec.github.io/authomatic.

Features
========

*	Loosely coupled.
*	Tiny but powerful interface.
*	The |pyopenid|_ library is the only **optional** dependency.
*	CSRF protection.
*	**Framework agnostic** thanks to adapters.
	Out of the box support for **Django**, **Flask** and **Webapp2**. 
*	Ready to accommodate future authorization / authentication protocols.
*	Makes calls to provider APIs a breeze.
*	Supports asynchronous requests.
*	JavaScript library as a bonus.
*	Out of the box support for:

	*	|oauth1|_ providers: **Bitbucket**, **Flickr**, **Meetup**, **Plurk**, **Twitter**,
		**Tumblr**, **UbuntuOne**, **Vimeo**, **Xero** and **Yahoo**.
	*	|oauth2|_ providers: **Behance**, **Bitly**, **Cosm**, **DeviantART**, **Facebook**,
		**Foursquare**, **GitHub**, **Google**, **LinkedIn**, **PayPal**, **Reddit**, **Viadeo**,
		**VK**, **WindowsLive**, **Yammer** and **Yandex**.
	*	|pyopenid|_ and |gae|_ based |openid|_.

.. note::

	To cool your excitement down a little bit,
	the library is in its **very early stage**
	and there are practically **no tests**!

License and Requirements
========================

The package is licensed under `MIT license <http://en.wikipedia.org/wiki/MIT_License>`_ 
and requires Python 2.7.

Live Demo
=========

There is a |gae| based live demo app running at
http://authomatic-example.appspot.com which makes use of most of the features.

Contribute
==========

.. image:: http://badge.waffle.io/peterhudec/authomatic.png
   :target: http://waffle.io/peterhudec/authomatic
   :alt: Stories in Ready

Contributions of any kind are very welcome.
The project is hosted on `GitHub <https://github.com/peterhudec/authomatic>`_.
If you find this library useful and are using it in your projects,
please don't be shy and leave a comment about your use case on the
`Authomatic use cases <https://github.com/peterhudec/authomatic/issues/1>`_ issue.

Usage
=====

Read the exhaustive documentation at http://peterhudec.github.io/authomatic.
