Simple Example
--------------

In this tutorial we will create a simple |gae|_ |webapp2|_ application
that will be able to log the **user** in with Facebook, Twitter and |openid|_
and retrieve the **user's** 5 most recent tweets/statuses.

First create the :doc:`/reference/config` dictionary:

.. literalinclude:: ../../../examples/gae/simple/config-template.py

Create ``main.py`` file and import what's needed. We don't need much.

.. literalinclude:: ../../../examples/gae/simple/main.py
   :language: python
   :lines: 1-6

Add a simple request handler which accepts ``GET`` and ``POST`` HTTP methods and
recieves the ``provider_name`` URL variable.

.. literalinclude:: ../../../examples/gae/simple/main.py
   :language: python
   :lines: 9, 13
   
Log the **user** in by calling the :func:`.authomatic.login` function inside the handler.
You must pass it an :doc:`adapter for your framework </reference/adapters>`,
in our case the :class:`.Webapp2Adapter`
and one of the *provider names* that you defined in the :doc:`/reference/config`,
which we get from the URL path of the request.

The function will redirect the **user** to the specified **provider**
to prompt **him/her** for consent and redirect **him/her** back to this handler.

.. literalinclude:: ../../../examples/gae/simple/main.py
   :language: python
   :lines: 16-17

If the *login procedure* is over :func:`.authomatic.login` returns a :class:`.LoginResult`.

.. warning::
   
   Do not write anything to the response unless the *login procedure* is over!
   The :func:`authomatic.login` either returns ``None``,
   which means that the *login procedure* si still pending,
   or a :class:`.LoginResult` which means that the *login procedure* is over.

.. literalinclude:: ../../../examples/gae/simple/main.py
   :language: python
   :lines: 20-22

Hopefully there is no :attr:`.LoginResult.error` but rather the :attr:`.LoginResult.user`.
Most of the **providers** don't provide **user** info on login.
To get more **user** info we need to call the :meth:`.User.update` method.

.. literalinclude:: ../../../examples/gae/simple/main.py
   :language: python
   :lines: 24, 26, 28, 33-34
   
Now we can welcome the **user** by name.

.. literalinclude:: ../../../examples/gae/simple/main.py
   :language: python
   :lines: 37-39

Seems like we're done, but we can do more:

If there are :class:`credentials <.core.Credentials>` the **user** has logged in with an
:class:`AuthorisationProvider <.providers.AuthorisationProvider>`
i.e. |oauth1|_ or |oauth2|_ and we can access **his/her** **protected resources**.

.. literalinclude:: ../../../examples/gae/simple/main.py
   :language: python
   :lines: 45

Each **provider** has it's specific API.
Let's first get the **user's** five most recent **Facebook** statuses.

.. literalinclude:: ../../../examples/gae/simple/main.py
   :language: python
   :lines: 48-49

Prepare the `Facebook Graph API <http://developers.facebook.com/docs/reference/api/>`_ URL.

.. literalinclude:: ../../../examples/gae/simple/main.py
   :language: python
   :lines: 52-53

Access the **protected resource** of the **user** at that URL.

.. literalinclude:: ../../../examples/gae/simple/main.py
   :language: python
   :lines: 56

Parse the response. The :attr:`.Response.data` is a data structure (list or dictionary)
parsed from the :attr:`.Response.content` which usually is JSON.

.. literalinclude:: ../../../examples/gae/simple/main.py
   :language: python
   :lines: 58-76

Do the same with Twitter.

.. literalinclude:: ../../../examples/gae/simple/main.py
   :language: python
   :lines: 78-103

That's it for the *Login* handler.

Now just for convenience that we don't have to enter all the URLs manualy
let's create a *Home* handler.

.. literalinclude:: ../../../examples/gae/simple/main.py
   :language: python
   :lines: 107-108

Create links to our *Login* handler.

.. literalinclude:: ../../../examples/gae/simple/main.py
   :language: python
   :lines: 111-112

Create **OpenID** forms where the **user** can specify **his/her** **claimed ID**.
The library by default extracts the identifier from the query string ``id`` parameter,
but you can change its name to whatever you want.

.. literalinclude:: ../../../examples/gae/simple/main.py
   :language: python
   :lines: 116-122, 124-129

Route URLs to your handlers.

.. literalinclude:: ../../../examples/gae/simple/main.py
   :language: python
   :lines: 133-134

Very important, you must call the :func:`authomatic.setup` and pass it at least
the :doc:`/reference/config` and a random secret string used for session and CSRF token generation.

.. literalinclude:: ../../../examples/gae/simple/main.py
   :language: python
   :lines: 136-137

Finally instantiate the WSGI application.

.. literalinclude:: ../../../examples/gae/simple/main.py
   :language: python
   :lines: 140

Don't forget to set up the ``app.yaml`` file.

.. literalinclude:: ../../../examples/gae/simple/app.yaml
   :language: yaml

And here is the complete app:

.. literalinclude:: ../../../examples/gae/simple/main.py