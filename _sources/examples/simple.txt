Simple |webapp2| |gae| Example 
------------------------------

.. seo-description::
   
   A simple tutorial where we create a Google App Engine app which can log users
   in with Facebook, Twitter and OpenID and read their recent statuses.

In this tutorial we will create a simple |gae|_ |webapp2|_ application
that will be able to log **users** in with Facebook, Twitter and |openid|_
and retrieve their 5 most recent tweets/statuses.

You can download all the source files we are about to create
`here <https://github.com/peterhudec/authomatic/tree/master/examples/gae/simple>`__.

First create the :doc:`/reference/config` dictionary where you set up all the providers you want to use.
Yo will need the ``consumer_key`` and ``consumer_secret`` which you can get
`here <https://developers.facebook.com/apps>`__ for Facebook and
`here <https://dev.twitter.com/apps>`__ for Twitter.

.. note::
   
   Facebook and other |oauth2| providers require a **redirect URI**
   which should be the URL of the *login request handler*
   which we will create in this tutorial and whose walue in our case will be
   ``http://[hostname]:[port]/login/fb`` for Facebook.

.. literalinclude:: ../../../examples/gae/simple/config-template.py

Create ``main.py`` file and import what's needed.

.. literalinclude:: ../../../examples/gae/simple/main.py
   :language: python
   :lines: 1-7

Make an instance of the :class:`.Authomatic` class and pass
the :doc:`/reference/config` together with a random secret string
used for session and CSRF token generation to it's constructor.

.. literalinclude:: ../../../examples/gae/simple/main.py
   :language: python
   :lines: 10

Create a simple request handler which accepts ``GET`` and ``POST`` HTTP methods and
receives the ``provider_name`` URL variable.

.. literalinclude:: ../../../examples/gae/simple/main.py
   :language: python
   :lines: 13, 17
   
Log the **user** in by calling the :meth:`.Authomatic.login` method inside the handler.
You must pass it an :doc:`adapter for your framework </reference/adapters>`,
in our case the :class:`.Webapp2Adapter`
and one of the *provider names* that you defined in the :doc:`/reference/config`,
which we get from the URL path of the request.

The method will redirect the **user** to the specified **provider**
to prompt **him/her** for consent and redirect **him/her** back to this handler.

.. literalinclude:: ../../../examples/gae/simple/main.py
   :language: python
   :lines: 20

The *login procedure* is over when :meth:`.Authomatic.login` returns a :class:`.LoginResult`.

.. warning::
   
   Do not write anything to the response unless the *login procedure* is over!
   The :meth:`.Authomatic.login` either returns ``None``,
   which means that the *login procedure* si still pending,
   or a :class:`.LoginResult` which means that the *login procedure* is over.

.. literalinclude:: ../../../examples/gae/simple/main.py
   :language: python
   :lines: 23, 25

Hopefully there is no :attr:`.LoginResult.error` but rather the :attr:`.LoginResult.user`.
Most of the **providers** don't provide **user** info on login.
To get more **user** info we need to call the :meth:`.User.update` method.

.. literalinclude:: ../../../examples/gae/simple/main.py
   :language: python
   :lines: 27, 29, 31, 36-37
   
Now we can welcome the **user** by name.

.. literalinclude:: ../../../examples/gae/simple/main.py
   :language: python
   :lines: 40-42

Seems like we're done, but we can do more:

If there are :class:`credentials <.core.Credentials>` the **user** has logged in with an
:class:`AuthorizationProvider <.providers.AuthorizationProvider>`
i.e. |oauth1|_ or |oauth2|_ and we can access **his/her** **protected resources**.

.. literalinclude:: ../../../examples/gae/simple/main.py
   :language: python
   :lines: 48

Each **provider** has it's specific API.
Let's first get the **user's** five most recent **Facebook** statuses.

.. literalinclude:: ../../../examples/gae/simple/main.py
   :language: python
   :lines: 51-52

Prepare the `Facebook Graph API <http://developers.facebook.com/docs/reference/api/>`__ URL.

.. literalinclude:: ../../../examples/gae/simple/main.py
   :language: python
   :lines: 55-56

Access the **protected resource** of the **user** at that URL.

.. literalinclude:: ../../../examples/gae/simple/main.py
   :language: python
   :lines: 59

Parse the response. The :attr:`.Response.data` is a data structure (list or dictionary)
parsed from the :attr:`.Response.content` which usually is JSON.

.. literalinclude:: ../../../examples/gae/simple/main.py
   :language: python
   :lines: 61-79

Do the same with Twitter.

.. literalinclude:: ../../../examples/gae/simple/main.py
   :language: python
   :lines: 81-107

That's it for the *Login* handler.

Now just for convenience that we don't have to enter all the URLs manually
let's create a *Home* handler.

.. literalinclude:: ../../../examples/gae/simple/main.py
   :language: python
   :lines: 111-112

Create links to our *Login* handler.

.. literalinclude:: ../../../examples/gae/simple/main.py
   :language: python
   :lines: 115-116

Create **OpenID** forms where the **user** can specify **his/her** **claimed ID**.
The library by default extracts the identifier from the query string ``id`` parameter,
but you can change its name to whatever you want.

.. literalinclude:: ../../../examples/gae/simple/main.py
   :language: python
   :lines: 120-126, 128-133

Route URLs to your handlers.

.. literalinclude:: ../../../examples/gae/simple/main.py
   :language: python
   :lines: 137-138

Finally instantiate the WSGI application.

.. literalinclude:: ../../../examples/gae/simple/main.py
   :language: python
   :lines: 141

Don't forget to set up the ``app.yaml`` file.

.. literalinclude:: ../../../examples/gae/simple/app.yaml
   :language: yaml

That's it. Now just run the application.

.. code-block:: bash
   
   $ python dev_appserver.py [path to the root folder of this app]

.. include:: twitter-localhost.rst

And here is the complete app. Remember that you can download all the files we just created from
`GitHub <https://github.com/peterhudec/authomatic/tree/master/examples/gae/simple>`__.

.. literalinclude:: ../../../examples/gae/simple/main.py
