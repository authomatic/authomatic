Simple |django| Example
-----------------------

:description: A simple tutorial where we create a Django app which can log users in with Facebook, Twitter and OpenID and read their recent statuses.

In this tutorial we will create a simple |django|_ application
that will be able to log **users** in with Facebook, Twitter and |openid|_
and retrieve their 5 most recent tweets/statuses.

You can download all the source files we are about to create
`here <https://github.com/authomatic/authomatic/tree/master/examples/django>`__.

First create a new |django|_ project named *example*.

.. code-block:: bash

   $ django-admin.py startproject example

Inside the newly created *example* project create a new application named *simple*.

.. code-block:: bash

   $ cd example
   $ python manage.py startapp simple
   $ cd simple

Open the ``example/simple/urls.py`` module and map the ``/`` root URL to the ``home`` view
and the ``/login/[provider_name]`` URL to the ``login`` view.
We will create the views later.

.. literalinclude:: ../../../examples/django/example/simple/urls.py
   :language: python
   :emphasize-lines: 8-9

We also need to include the ``simple`` app in the ``INSTALLED_APPS`` tuple
in the ``example/example/settings.py`` module.

.. literalinclude:: ../../../examples/django/example/example/settings.py
   :language: python
   :lines: 1, 3, 112-124
   :emphasize-lines: 14

And create a route to the app in the ``example/example/urls.py`` module.

.. literalinclude:: ../../../examples/django/example/example/urls.py
   :language: python
   :lines: 1-4, 9, 20-21
   :emphasize-lines: 6

Now in the ``example/simple`` directory create the ``config.py`` module
with the :doc:`/reference/config` dictionary where you set up all the providers you want to use.
You will need the ``consumer_key`` and ``consumer_secret`` which you can get
`here <https://developers.facebook.com/apps>`__ for Facebook and
`here <https://dev.twitter.com/apps>`__ for Twitter.

.. note::

   Facebook and other |oauth2| providers require a **redirect URI**
   which should be the URL of the *login view*
   which we will create in this tutorial and whose walue in our case will be
   ``https://[hostname]/simple/login/fb`` for Facebook.


.. literalinclude:: ../../../examples/django/example/simple/config-template.py

The rest happens in the ``example/simple/views.py`` file. Open it and import what's needed.

.. literalinclude:: ../../../examples/django/example/simple/views.py
   :language: python
   :lines: 1-7

Make an instance of the :class:`.Authomatic` class and pass
the :doc:`/reference/config` together with a random secret string
used for session and CSRF token generation to it's constructor.

.. literalinclude:: ../../../examples/django/example/simple/views.py
   :language: python
   :lines: 9

Create the *home* view with an OpenID form and links to the *login* view
which we are going to create next.

.. literalinclude:: ../../../examples/django/example/simple/views.py
   :language: python
   :lines: 11, 13-20

Create the *login* view which should receive the ``provider_name`` URL variable.
Inside the view instantiate the :class:`django.http.HttpResponse` class.

.. literalinclude:: ../../../examples/django/example/simple/views.py
   :language: python
   :lines: 22, 24

Now just Log the **user** in by calling the :meth:`.Authomatic.login` method inside the *login* view.
You must pass it the :class:`.DjangoAdapter`
and the ``provider_name`` URL variable.
The :class:`.DjangoAdapter` needs instances of :class:`django.http.HttpRequest`
and :class:`django.http.HttpResponse`.
The method will redirect the **user** to the specified **provider**
to prompt **them** for consent and redirect **them** back to this view.

.. literalinclude:: ../../../examples/django/example/simple/views.py
   :language: python
   :lines: 27

The *login procedure* is over when :meth:`.Authomatic.login` returns a :class:`.LoginResult`.

.. warning::

   Do not write anything to the response unless the *login procedure* is over!
   The :meth:`.Authomatic.login` either returns ``None``,
   which means that the *login procedure* si still pending,
   or a :class:`.LoginResult` which means that the *login procedure* is over.

.. literalinclude:: ../../../examples/django/example/simple/views.py
   :language: python
   :lines: 31, 33

Hopefully there is no :attr:`.LoginResult.error` but rather the :attr:`.LoginResult.user`.
Most of the **providers** don't provide **user** info on login.
To get more **user** info we need to call the :meth:`.User.update` method.

.. literalinclude:: ../../../examples/django/example/simple/views.py
   :language: python
   :lines: 35, 37, 39, 44-45

Now we can welcome the **user** by name.

.. literalinclude:: ../../../examples/django/example/simple/views.py
   :language: python
   :lines: 48-50

Seems like we're done, but we can do more:

If there are :class:`credentials <.core.Credentials>` the **user** has logged in with an
:class:`AuthorizationProvider <.providers.AuthorizationProvider>`
i.e. |oauth1|_ or |oauth2|_ and we can access **their** **protected resources**.

.. literalinclude:: ../../../examples/django/example/simple/views.py
   :language: python
   :lines: 56

Each **provider** has it's specific API.
Let's first get the **user's** five most recent **Facebook** statuses.

.. literalinclude:: ../../../examples/django/example/simple/views.py
   :language: python
   :lines: 59-60

Prepare the `Facebook Graph API <https://developers.facebook.com/docs/reference/api/>`_ URL.

.. literalinclude:: ../../../examples/django/example/simple/views.py
   :language: python
   :lines: 63-64

Access the **protected resource** of the **user** at that URL.

.. literalinclude:: ../../../examples/django/example/simple/views.py
   :language: python
   :lines: 67

Parse the response. The :attr:`.Response.data` is a data structure (list or dictionary)
parsed from the :attr:`.Response.content` which usually is JSON.

.. literalinclude:: ../../../examples/django/example/simple/views.py
   :language: python
   :lines: 69-87

Do the same with Twitter.

.. literalinclude:: ../../../examples/django/example/simple/views.py
   :language: python
   :lines: 89-115

Finally return the ``response`` instance.

.. literalinclude:: ../../../examples/django/example/simple/views.py
   :language: python
   :lines: 117

Run the app and navigate to ``https://[hostname]/simple`` in your browser.

.. code-block:: bash

   $ python manage.py runserver

.. include:: twitter-localhost.rst

And here is the complete ``example/simple/views.py`` module.
Remember that you can download all the files we just created from
`GitHub <https://github.com/authomatic/authomatic/tree/master/examples/django>`_.

.. literalinclude:: ../../../examples/django/example/simple/views.py
