Simple Example
--------------

In this tutorial we will create a simple |gae|_ |webapp2|_ application
that will be able to log the **user** in with Facebook, Twitter and |openid|
and retrieve the **user's** 5 most recent tweets/statuses.

First create the :doc:`/reference/config` dictionary:

.. literalinclude:: ../../../examples/gae/simple/config-template.py

Create ``main.py`` file and import what's needed. We don't need much.

.. literalinclude:: ../../../examples/gae/simple/main.py
   :language: python
   :lines: 1-5

Add a simple request handler which accepts ``GET`` and ``POST`` HTTP methods and
recieves the ``provider_name`` URL variable.

.. literalinclude:: ../../../examples/gae/simple/main.py
   :language: python
   :lines: 8, 12-13
   
Log the **user** in by calling the :func:`.authomatic.login` function.
This will redirect the **user** to the specified **provider** to prompt **him/her** for consent and
redirect **him/her** back to this handler.

.. literalinclude:: ../../../examples/gae/simple/main.py
   :language: python
   :lines: 16
   
The login procedure is over if there is either a :attr:`.LoginResult.error` or :attr:`.LoginResult.user`.
You also can test the status of the *login procedure* with :attr:`.LoginResult.pending`.

.. literalinclude:: ../../../examples/gae/simple/main.py
   :language: python
   :lines: 18, 20

If there are no errors there must be a :class:`User <.core.User>` object.
We must update it if we need properties like **name** or **email** if the
**user** logged in with |oauth2|_ or |oauth1|_ **provider**.  

.. literalinclude:: ../../../examples/gae/simple/main.py
   :language: python
   :lines: 22, 27
   
Welcome the **user**.  

.. literalinclude:: ../../../examples/gae/simple/main.py
   :language: python
   :lines: 30-32

Seems like we're done, but we can do more...

If there are :class:`credentials <.core.Credentials>` the **user** has logged in with an
:class:`AuthorisationProvider <.providers.AuthorisationProvider>`
i.e. |oauth1|_ or |oauth2|_ and we can access **his/her** **protected resources**.

.. literalinclude:: ../../../examples/gae/simple/main.py
   :language: python
   :lines: 38

Each **provider** has it's specific API.
Let's first get the **user's** five most recent **Facebook** statuses.

.. literalinclude:: ../../../examples/gae/simple/main.py
   :language: python
   :lines: 41, 43

Prepare the `Facebook Graph API <http://developers.facebook.com/docs/reference/api/>`_ URL.

.. literalinclude:: ../../../examples/gae/simple/main.py
   :language: python
   :lines: 46-47

Request the **provider** to access the **protected resource** of the **user**  at that URL.

.. literalinclude:: ../../../examples/gae/simple/main.py
   :language: python
   :lines: 50

Parse the response. The :attr:`.Response.data` is a data structure (list or dictionary)
parsed from the :attr:`.Response.content` which is usually JSON.

.. literalinclude:: ../../../examples/gae/simple/main.py
   :language: python
   :lines: 52, 54-70

Do the same with Twitter.

.. literalinclude:: ../../../examples/gae/simple/main.py
   :language: python
   :lines: 72, 74-75, 77-78, 80-81, 83-98

That's it for the *Login* handler.

Now just for convenience that we don't have to enter all the URLs manualy
let's create a *Home* handler.

.. literalinclude:: ../../../examples/gae/simple/main.py
   :language: python
   :lines: 102, 104

Create links to our *Login* handler.

.. literalinclude:: ../../../examples/gae/simple/main.py
   :language: python
   :lines: 107-108

Create **OpenID** forms where the **user** can specify **his/her** **claimed ID**.
The library by default extracts the identifier from the query string ``id`` parameter,
but you can change its name to whatever you want.

.. literalinclude:: ../../../examples/gae/simple/main.py
   :language: python
   :lines: 112-118, 120-125

Route URLs to your handlers.

.. literalinclude:: ../../../examples/gae/simple/main.py
   :language: python
   :lines: 129-130

Create the WSGI application.

.. literalinclude:: ../../../examples/gae/simple/main.py
   :language: python
   :lines: 133

Finally, most important!!! Wrapp the app in :func:`authomatic.middleware`,
pass it the :doc:`/reference/config` and some random secret string.

.. literalinclude:: ../../../examples/gae/simple/main.py
   :language: python
   :lines: 136-

And here is the complete app:

.. literalinclude:: ../../../examples/gae/simple/main.py

Don't forget to set up the ``app.yaml`` file.

.. literalinclude:: ../../../examples/gae/simple/app.yaml
   :language: yaml