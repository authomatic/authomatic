Advanced |webapp2| |gae| Example
--------------------------------

.. seo-description::
   
   An advanced tutorial where we create a Google App Engine app
   where users can log in with Facebook, Twitter and OpenID and post statuses.

In this tutorial we will create a |gae|_ |webapp2|_ application
that will be able to log **users** in with Facebook, Twitter and |openid|_
and we will use the :class:`.Credentials` of an **authenticated user** to
post tweets and Facebook statuses on the **user's** behalf.

You can download all the source files we are about to create
`here <https://github.com/peterhudec/authomatic/tree/master/examples/gae/credentials>`_.

First create the :doc:`/reference/config` dictionary where you set up all the providers you want to use.
Yo will need the ``consumer_key`` and ``consumer_secret`` which you can get
`here <https://developers.facebook.com/apps>`_ for Facebook and
`here <https://dev.twitter.com/apps>`_ for Twitter.

.. note::
   
   Facebook and other |oauth2| providers require a **redirect URI**
   which should be the URL of the *login request handler*
   which we will create in this tutorial and whose walue in our case will be
   ``http://[hostname]:[port]/login/fb`` for Facebook.

.. literalinclude:: ../../../examples/gae/credentials/config-template.py
   :language: python

Create the ``main.py`` module and import what's needed.

.. literalinclude:: ../../../examples/gae/credentials/main.py
   :language: python
   :lines: 1-9

Make an instance of the :class:`.Authomatic` class and pass
the :doc:`/reference/config` together with a random secret string
used for session and CSRF token generation to it's constructor.

.. literalinclude:: ../../../examples/gae/credentials/main.py
   :language: python
   :lines: 12

Create a simple request handler which accepts ``GET`` and ``POST`` HTTP methods and
receives the ``provider_name`` URL variable.
Log the **user** in by calling the :meth:`.Authomatic.login` method.

.. literalinclude:: ../../../examples/gae/credentials/main.py
   :language: python
   :lines: 14, 15, 18

If there is :attr:`.LoginResult.user`, the *login procedure* was successful
and we can welcome the **user**.

.. literalinclude:: ../../../examples/gae/credentials/main.py
   :language: python
   :lines: 20-23

Save the **user's** name and ID to cookies so we can use them in other handlers.
We use cookies only for simplicity of the example,
in real app you will probably use some *User* datamodel.

.. literalinclude:: ../../../examples/gae/credentials/main.py
   :language: python
   :lines: 26-27

If the **user** has logged in with Facebook or Twitter, **he/she** gave us :class:`.Credentials`.

.. literalinclude:: ../../../examples/gae/credentials/main.py
   :language: python
   :lines: 29

You can serialize the :class:`.Credentials` into a lightweight URL-safe string.
Store also the serialized credentials to a cookie.

.. literalinclude:: ../../../examples/gae/credentials/main.py
   :language: python
   :lines: 31-32

Store also the possible error message to a cookie.

.. literalinclude:: ../../../examples/gae/credentials/main.py
   :language: python
   :lines: 34-35

Redirect the **user** to the *Home* handler which we are going to create next.

.. literalinclude:: ../../../examples/gae/credentials/main.py
   :language: python
   :lines: 37

The *Home* handler only needs a ``GET`` method.

.. literalinclude:: ../../../examples/gae/credentials/main.py
   :language: python
   :lines: 40-41

Create links to the *Login* handler.

.. literalinclude:: ../../../examples/gae/credentials/main.py
   :language: python
   :lines: 43-44

Retrieve the stored values from cookies.

.. literalinclude:: ../../../examples/gae/credentials/main.py
   :language: python
   :lines: 47-50

Handle possible errors.

.. literalinclude:: ../../../examples/gae/credentials/main.py
   :language: python
   :lines: 52-53

If there is no error, there must be a **user** ID.

.. literalinclude:: ../../../examples/gae/credentials/main.py
   :language: python
   :lines: 54-55

Let's look at what we can do with the :class:`.Credentials`.

.. literalinclude:: ../../../examples/gae/credentials/main.py
   :language: python
   :lines: 57

We can deserialize them.

.. literalinclude:: ../../../examples/gae/credentials/main.py
   :language: python
   :lines: 59

They know the **provider** name which we defined in the :doc:`/reference/config`.

.. literalinclude:: ../../../examples/gae/credentials/main.py
   :language: python
   :lines: 61-65

:class:`.Credentials` issued by |oauth2|_ providers have limited lifetime.
We can test whether they are still valid.

.. literalinclude:: ../../../examples/gae/credentials/main.py
   :language: python
   :lines: 67

Whether they expire soon.

.. literalinclude:: ../../../examples/gae/credentials/main.py
   :language: python
   :lines: 68

The remaining number of seconds till they expire.

.. note::
   
   If the number is negative, the :class:`.Credentials` will never expire.

.. literalinclude:: ../../../examples/gae/credentials/main.py
   :language: python
   :lines: 69

Their expiration date.

.. note::
   
   If :class:`.Credentials` will never expire it returns ``None``.

.. literalinclude:: ../../../examples/gae/credentials/main.py
   :language: python
   :lines: 70

We can refresh the :class:`.Credentials` without the **user** while they are valid.
If they are expired we only can get new :class:`.Credentials` by repeating the *login procedure*
with :meth:`.Authomatic.login`.

Inform the **user** about **his/her** :class:`.Credentials` and create links to
*Refresh*, *Action* and *Logout* handlers, which we are going to create next.

.. literalinclude:: ../../../examples/gae/credentials/main.py
   :language: python
   :lines: 72-97

Create the *Refresh* handler, retrieve the serialized :class:`.Credentials` from
the cookie, deserialize them and get their expiration date.

.. literalinclude:: ../../../examples/gae/credentials/main.py
   :language: python
   :lines: 100-106

Refresh the :class:`.Credentials` with the :meth:`.Credentials.refresh` method.
It returns a :class:`.Response object`, but only if the :class:`.Credentials` support refreshment.
Otherwise the method returns ``None``.

.. note::
   
   Only |oauth2| :class:`.Credentials` support refreshment but it also depends on the **provider's**
   implementation, e.g. Facebook allows you to refresh :class:`.Credentials` only if you requested the
   ``offline_access`` scope in the :doc:`/reference/config`.

.. literalinclude:: ../../../examples/gae/credentials/main.py
   :language: python
   :lines: 108-131

The most interesting things will happen in the *Action* handler.
Let's first create a method for ``GET`` requests which will accept the ``provider_name`` URL variable. 
Inside create a simple HTML form which submits to this handler's ``POST`` method.

.. literalinclude:: ../../../examples/gae/credentials/main.py
   :language: python
   :lines: 134-148

In the ``POST`` method, retrieve the message from POST parameters and the values from cookies.

.. literalinclude:: ../../../examples/gae/credentials/main.py
   :language: python
   :lines: 150-152, 154-156

Let's first post a status to the **user's** Facebook timeline by accessing the
`Facebook Graph API <http://developers.facebook.com/docs/reference/api/>`_ endpoint.

.. note::
   
   You need to include the ``"publish_stream"`` scope in the ``"fb"`` section of the config
   to be able to post to the **user's** timeline.

Prepare the URL.

.. literalinclude:: ../../../examples/gae/credentials/main.py
   :language: python
   :lines: 158, 160

Access the **protected resource** of the **user** by calling the :meth:`.Authomatic.access` method.
You must pass it the :class:`.Credentials` (normal or serialized) and the URL.
The URL can contain query string parameters, but
you can also pass them to the method as a dictionary.
The method returns a :class:`.Response` object.

.. literalinclude:: ../../../examples/gae/credentials/main.py
   :language: python
   :lines: 163-165

Parse the :class:`.Response`. The :attr:`.Response.data` is a data structure (list or dictionary)
parsed from the :attr:`.Response.content` which usually is JSON.

.. literalinclude:: ../../../examples/gae/credentials/main.py
   :language: python
   :lines: 168-178

Do the same with Twitter.

.. note::
   
   You need to set the *Application Type* of your `Twitter app <https://dev.twitter.com/apps>`_
   to *Read and Write* to be able to post tweets on the **user's** behalf.

.. literalinclude:: ../../../examples/gae/credentials/main.py
   :language: python
   :lines: 180-203

Let the **user** repeat the action.

.. literalinclude:: ../../../examples/gae/credentials/main.py
   :language: python
   :lines: 206-211

The *Logout* handler is pretty simple. We just need to delete all those cookies we set
and redirect the **user** to the *Home* handler.

.. literalinclude:: ../../../examples/gae/credentials/main.py
   :language: python
   :lines: 214-215, 217-219, 222

Finally create routes to all those handlers,

.. literalinclude:: ../../../examples/gae/credentials/main.py
   :language: python
   :lines: 226-230

and instantiate the |webapp2| WSGI application.

.. literalinclude:: ../../../examples/gae/credentials/main.py
   :language: python
   :lines: 233

Don't forget to create the ``app.yaml`` file.

.. literalinclude:: ../../../examples/gae/credentials/app.yaml
   :language: yaml

That's it. Now just run the application.

.. code-block:: bash
   
   $ python dev_appserver.py [path to the root folder of this app]

.. include:: twitter-localhost.rst

And here is the complete app. Remember that you can download all the files we just created from
`GitHub <https://github.com/peterhudec/authomatic/tree/master/examples/gae/credentials>`_.

.. literalinclude:: ../../../examples/gae/credentials/main.py
   :language: python

