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
   :lines: 1-7

Pass the :doc:`/reference/config` to :func:`authomatic.setup` together with
a random secret string used for session and CSRF token generation.

.. literalinclude:: ../../../examples/gae/simple/main.py
   :language: python
   :lines: 10

Add a simple request handler which accepts ``GET`` and ``POST`` HTTP methods and
receives the ``provider_name`` URL variable.

.. literalinclude:: ../../../examples/gae/simple/main.py
   :language: python
   :lines: 13, 17
   
Log the **user** in by calling the :func:`.authomatic.login` function inside the handler.
You must pass it an :doc:`adapter for your framework </reference/adapters>`,
in our case the :class:`.Webapp2Adapter`
and one of the *provider names* that you defined in the :doc:`/reference/config`,
which we get from the URL path of the request.

The function will redirect the **user** to the specified **provider**
to prompt **him/her** for consent and redirect **him/her** back to this handler.

.. literalinclude:: ../../../examples/gae/simple/main.py
   :language: python
   :lines: 20

The *login procedure* is over when :func:`.authomatic.login` returns a :class:`.LoginResult`.

.. warning::
   
   Do not write anything to the response unless the *login procedure* is over!
   The :func:`authomatic.login` either returns ``None``,
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

Prepare the `Facebook Graph API <http://developers.facebook.com/docs/reference/api/>`_ URL.

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
   :lines: 144

Don't forget to set up the ``app.yaml`` file.

.. literalinclude:: ../../../examples/gae/simple/app.yaml
   :language: yaml

And here is the complete app:

.. literalinclude:: ../../../examples/gae/simple/main.py
