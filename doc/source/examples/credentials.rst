Credentials
-----------

In this tutorial we will create a |gae|_ |webapp2|_ application
that will be able to log the **user** in with Facebook, Twitter and |openid|_
and we will use the **user's** :class:`.Credentials` to
post tweets and Facebook statuses on the **user's** behalf.

First create the :doc:`/reference/config` dictionary.

.. literalinclude:: ../../../examples/gae/credentials/config-template.py
   :language: python

Create the ``main.py`` module and import what's needed.

.. literalinclude:: ../../../examples/gae/credentials/main.py
   :language: python
   :lines: 1-8

Add a simple request handler which accepts ``GET`` and ``POST`` HTTP methods and
recieves the ``provider_name`` URL variable.
Log the **user** in by calling the :func:`.authomatic.login` function.

.. literalinclude:: ../../../examples/gae/credentials/main.py
   :language: python
   :lines: 11, 12, 15

If there is :attr:`.LoginResult.user`, the *login procedure* was successful
and we can welcome the **user**.

.. literalinclude:: ../../../examples/gae/credentials/main.py
   :language: python
   :lines: 17-20

Save the **user's** name and ID to cookies so we can use them in other handlers.
We use cookies only for simplicity of the example,
in real app you will probably use some *User* datamodel.

.. literalinclude:: ../../../examples/gae/credentials/main.py
   :language: python
   :lines: 23-24

If the **user** has logged in with Facebook or Twitter, **he/she** gave us :class:`.Credentials`.

.. literalinclude:: ../../../examples/gae/credentials/main.py
   :language: python
   :lines: 26

You can serialize the :class:`.Credentials` into a lightweight URL-safe string.
Store also the serialized credentials to a cookie.

.. literalinclude:: ../../../examples/gae/credentials/main.py
   :language: python
   :lines: 28-29

Store also the possible error message to a cookie.

.. literalinclude:: ../../../examples/gae/credentials/main.py
   :language: python
   :lines: 31-32

Redirect the **user** to the *Home* handler which we are going to create next.

.. literalinclude:: ../../../examples/gae/credentials/main.py
   :language: python
   :lines: 34

The *Home* handler only needs a ``GET`` method.

.. literalinclude:: ../../../examples/gae/credentials/main.py
   :language: python
   :lines: 37-38

Create links to the *Login* handler.

.. literalinclude:: ../../../examples/gae/credentials/main.py
   :language: python
   :lines: 40-41

Retrieve the stored values from cookies.

.. literalinclude:: ../../../examples/gae/credentials/main.py
   :language: python
   :lines: 44-47

Handle possible errors.

.. literalinclude:: ../../../examples/gae/credentials/main.py
   :language: python
   :lines: 49-50

If there is no error, there must be a **user** ID.

.. literalinclude:: ../../../examples/gae/credentials/main.py
   :language: python
   :lines: 51-52

Let's look at what we can do with the :class:`.Credentials`.

.. literalinclude:: ../../../examples/gae/credentials/main.py
   :language: python
   :lines: 54

We can deserialize them.

.. literalinclude:: ../../../examples/gae/credentials/main.py
   :language: python
   :lines: 56

They know the **provider** name which we defined in the :doc:`/reference/config`.

.. literalinclude:: ../../../examples/gae/credentials/main.py
   :language: python
   :lines: 58-62

:class:`.Credentials` issued by |oauth2| providers have limited lifetime.
We can test whether they are still valid.

.. literalinclude:: ../../../examples/gae/credentials/main.py
   :language: python
   :lines: 64

Whether they expire soon.

.. literalinclude:: ../../../examples/gae/credentials/main.py
   :language: python
   :lines: 65

The remaining number of seconds till they expire.

.. note::
   
   If the number is negative, the :class:`.Credentials` will never expire.

.. literalinclude:: ../../../examples/gae/credentials/main.py
   :language: python
   :lines: 66

Their expiration date.

.. note::
   
   If :class:`.Credentials` will never expire it returns ``None``.

.. literalinclude:: ../../../examples/gae/credentials/main.py
   :language: python
   :lines: 67

We can refresh the :class:`.Credentials` without the **user** while they are valid.
If they are expired we only can get new :class:`.Credentials` by repeating the *login procedure*
with :func:`authomatic.login`.

Inform the **user** about **his/her** :class:`.Credentials` and create links to
*Refresh*, *Action* and *Logout* handlers, which we are going to create next.

.. literalinclude:: ../../../examples/gae/credentials/main.py
   :language: python
   :lines: 69-92

Create the *Refresh* handler, retrieve the serialized :class:`.Credentials` from
the cookie, deserialize them and get their expiration date.

.. literalinclude:: ../../../examples/gae/credentials/main.py
   :language: python
   :lines: 95-100, 102

Refresh the :class:`.Credentials` with the :meth:`.Credentials.refresh` method.
It returns a :class:`.Response object`, but only if the :class:`.Credentials` support refreshment.
Otherwise the method returns ``None``.

.. note::
   
   Only |oauth2| :class:`.Credentials` support refreshment but it also depends on the **provider's**
   implementation, e.g. Facebook allows you to refresh :class:`.Credentials` only if you requested the
   ``offline_access`` scope in the :doc:`/reference/config`.

.. literalinclude:: ../../../examples/gae/credentials/main.py
   :language: python
   :lines: 104-127

The most interesting things will happen in the *Action* handler.
Let's first create a method for ``GET`` requests which will accept the ``provider_name`` URL variable. 
Inside create a simple HTML form which submits to this handler's ``POST`` method.

.. literalinclude:: ../../../examples/gae/credentials/main.py
   :language: python
   :lines: 130-144

In the ``POST`` method, retrieve the message from POST parameters and the values from cookies.

.. literalinclude:: ../../../examples/gae/credentials/main.py
   :language: python
   :lines: 146-148, 150-152

Let's first post a status to the **user's** Facebook timeline by accessing the
`Facebook Graph API <http://developers.facebook.com/docs/reference/api/>`_ endpoint.

.. note::
   
   You need to include the ``"publish_stream"`` scope in the ``"fb"`` section of the config
   to be able to post to the **user's** timeline.

Prepare the URL.

.. literalinclude:: ../../../examples/gae/credentials/main.py
   :language: python
   :lines: 154, 156

Access the **protected resource** of the **user** by calling the :func:`authomatic.access` function.
You must pass it the :class:`.Credentials` (normal or serialized) and the URL.
The URL can contain query string parameters, but
you can also pass them to the function as a dictionary.
The function returns a :class:`.Response` object.

.. literalinclude:: ../../../examples/gae/credentials/main.py
   :language: python
   :lines: 159-161

Parse the :class:`.Response`. The :attr:`.Response.data` is a data structure (list or dictionary)
parsed from the :attr:`.Response.content` which usually is JSON.

.. literalinclude:: ../../../examples/gae/credentials/main.py
   :language: python
   :lines: 164-174

Do the same with Twitter.

.. note::
   
   You need to set the *Application Type* of your `Twitter app <https://dev.twitter.com/apps>`_
   to *Read and Write* to be able to post tweets on the **user's** behalf.

.. literalinclude:: ../../../examples/gae/credentials/main.py
   :language: python
   :lines: 176-192

Let the **user** repeat the action.

.. literalinclude:: ../../../examples/gae/credentials/main.py
   :language: python
   :lines: 195-200

The *Logout* handler is pretty simple. We just need to delete all those cookies we set
and redirect the **user** to the *Home* handler.

.. literalinclude:: ../../../examples/gae/credentials/main.py
   :language: python
   :lines: 203-204, 206-208, 211

Finally create routes to all those handlers, ...

.. literalinclude:: ../../../examples/gae/credentials/main.py
   :language: python
   :lines: 215-219

Very important, you must call the :func:`authomatic.setup` and pass it at least
the :doc:`/reference/config` and a random secret string used for session and CSRF token generation.

.. literalinclude:: ../../../examples/gae/credentials/main.py
   :language: python
   :lines: 221

Finally instantiate the |webapp2| WSGI application.

.. literalinclude:: ../../../examples/gae/credentials/main.py
   :language: python
   :lines: 223

Don't forget to create the ``app.yaml`` file.

.. literalinclude:: ../../../examples/gae/credentials/app.yaml
   :language: yaml

And here is the complete app:

.. literalinclude:: ../../../examples/gae/credentials/main.py
   :language: python

