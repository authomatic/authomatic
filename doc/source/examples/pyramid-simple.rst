Simple |pyramid| Example
------------------------

:description: A simple tutorial where we create a Pyramid application which can log users in with Facebook, Twitter and OpenID and read their recent statuses.

In this tutorial we will create a simple |pyramid|_ application
that will be able to log **users** in with Facebook, Twitter and |openid|_
and retrieve their 5 most recent tweets/statuses.

You can download all the source files we are about to create
`here <https://github.com/authomatic/authomatic/tree/master/examples/pyramid/simple>`__.

First create the :doc:`/reference/config`
dictionary where you set up all the providers you want to use.
Yo will need the ``consumer_key`` and ``consumer_secret`` which you can get
`here <https://developers.facebook.com/apps>`__ for Facebook and
`here <https://dev.twitter.com/apps>`__ for Twitter.

.. note::

   Facebook and other |oauth2| providers require a **redirect URI**
   which should be the URL of the *login request view*
   which we will create in this tutorial and whose walue in our case will be
   ``https://[hostname]:[port]/login/fb`` for Facebook.

.. literalinclude:: ../../../examples/pyramid/simple/config-template.py

Create ``main.py`` file and import what's needed.

.. literalinclude:: ../../../examples/pyramid/simple/main.py
   :language: python
   :lines: 2-10

Make an instance of the :class:`.Authomatic` class and pass
the :doc:`/reference/config` together with a random secret string
used for session and CSRF token generation to it's constructor.

.. literalinclude:: ../../../examples/pyramid/simple/main.py
   :language: python
   :lines: 12

Create a simple *login* view.

.. literalinclude:: ../../../examples/pyramid/simple/main.py
   :language: python
   :lines: 15

Inside the *login* view create a :class:`pyramid.response.Response` instance which we need to pass to the :class:`.WebObAdapter`.

.. literalinclude:: ../../../examples/pyramid/simple/main.py
   :language: python
   :lines: 18

Get the ``provider_name`` URL variable.

.. literalinclude:: ../../../examples/pyramid/simple/main.py
   :language: python
   :lines: 21

Log the **user** in by calling the :meth:`.Authomatic.login` method inside the view.
You must pass it an :doc:`adapter for your framework </reference/adapters>`
and one of the *provider names* that you defined in the :doc:`/reference/config`,
which we get from the URL path of the request.
|pyramid| is based on |webob|_ so the :class:`.WebObAdapter` will do the job.
The method will redirect the **user** to the specified **provider**
to prompt **him/her** for consent and redirect **him/her** back to this view.

.. literalinclude:: ../../../examples/pyramid/simple/main.py
   :language: python
   :lines: 24

The *login procedure* is over when :meth:`.Authomatic.login` returns a :class:`.LoginResult`.

.. warning::

   Do not write anything to the response unless the *login procedure* is over!
   The :meth:`.Authomatic.login` either returns ``None``,
   which means that the *login procedure* si still pending,
   or a :class:`.LoginResult` which means that the *login procedure* is over.

.. literalinclude:: ../../../examples/pyramid/simple/main.py
   :language: python
   :lines: 27, 29

Hopefully there is no :attr:`.LoginResult.error` but rather :attr:`.LoginResult.user`.
Most of the **providers** don't provide **user** info on login.
To get more **user** info we need to call the :meth:`.User.update` method.

.. literalinclude:: ../../../examples/pyramid/simple/main.py
   :language: python
   :lines: 31, 33, 35, 40-41

Now we can welcome the **user** by name.

.. literalinclude:: ../../../examples/pyramid/simple/main.py
   :language: python
   :lines: 44-46

Seems like we're done, but we can do more:

If there are :class:`.Credentials` the **user** has logged in with an
:class:`.AuthorizationProvider` i.e. |oauth1|_ or |oauth2|_
and we can access **his/her** **protected resources**.

.. literalinclude:: ../../../examples/pyramid/simple/main.py
   :language: python
   :lines: 52

Each **provider** has it's specific API.
Let's first get the **user's** five most recent Facebook statuses.

.. literalinclude:: ../../../examples/pyramid/simple/main.py
   :language: python
   :lines: 55-56

Prepare the `Facebook Graph API <https://developers.facebook.com/docs/reference/api/>`_ URL.

.. literalinclude:: ../../../examples/pyramid/simple/main.py
   :language: python
   :lines: 59-60

Access the **protected resource** of the **user** at that URL.

.. literalinclude:: ../../../examples/pyramid/simple/main.py
   :language: python
   :lines: 63

Parse the response. The :attr:`.Response.data` is a data structure (list or dictionary)
parsed from the :attr:`.Response.content` which usually is JSON.

.. literalinclude:: ../../../examples/pyramid/simple/main.py
   :language: python
   :lines: 65-83

Do the same with Twitter.

.. literalinclude:: ../../../examples/pyramid/simple/main.py
   :language: python
   :lines: 85-111

Now this is **VERY IMPORTANT!** The *login* view **MUST** return the same response instance
which we passed to the :class:`.WebObAdapter`. Otherwise it just won't work.

.. literalinclude:: ../../../examples/pyramid/simple/main.py
   :language: python
   :lines: 114

That's it for the *login* view.

Now just for convenience that we don't have to enter all the URLs manually
let's create a *Home* view with an OpenID form and links to the *login* view.

.. literalinclude:: ../../../examples/pyramid/simple/main.py
   :language: python
   :lines: 117-125

Last bit is to configure the application.

.. literalinclude:: ../../../examples/pyramid/simple/main.py
   :language: python
   :lines: 128-139


That's it. Now just run the application and navigate your browser to ``http://127.0.0.1:8080`` or ``http://localhost:8080``.

.. code-block:: bash

   $ python main.py

.. include:: twitter-localhost.rst

And here is the complete app. Remember that you can download all the files we just created from
`GitHub <https://github.com/authomatic/authomatic/tree/master/examples/pyramid/simple>`_.

.. literalinclude:: ../../../examples/pyramid/simple/main.py
