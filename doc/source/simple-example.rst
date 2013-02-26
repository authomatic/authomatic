Simple Example
^^^^^^^^^^^^^^

A simple example is worth a thousand words:

First create the :doc:`reference/config` dictionary:

.. literalinclude:: ../../examples/gae/simple/config-template.py

Create ``main.py`` file and import what's needed. We don't need much.

.. literalinclude:: ../../examples/gae/simple/main.py
   :language: python
   :lines: 1-5

Add a simple request handler which accepts ``GET`` and ``POST`` HTTP methods and
recieves the ``provider_name`` URL variable.

.. literalinclude:: ../../examples/gae/simple/main.py
   :language: python
   :lines: 8, 12
   
Log the **user** in with :func:`.authomatic.login`.
This will redirect the **user** to the specified **provider** to prompt him/her for consent and
redirect him/her back to this handler.

.. literalinclude:: ../../examples/gae/simple/main.py
   :language: python
   :lines: 15
   
The login procedure is finished when there is a :class:`LoginResult <.core.LoginResult>`.

.. literalinclude:: ../../examples/gae/simple/main.py
   :language: python
   :lines: 17, 19
   
Check for errors.

.. literalinclude:: ../../examples/gae/simple/main.py
   :language: python
   :lines: 21, 23
   
If there are no errors there must be a :class:`User <.core.User>` object.
We must update it if we need properties like **name** or **email** when the
**user** logged in with |oauth2|_ or |oauth1|_ **provider**.  

.. literalinclude:: ../../examples/gae/simple/main.py
   :language: python
   :lines: 25, 30
   
Welcome the **user**.  

.. literalinclude:: ../../examples/gae/simple/main.py
   :language: python
   :lines: 33-35

Seems like we're done, but we can do more...

If there are :class:`credentials <.core.Credentials>` the **user** has logged in with an
:class:`AuthorisationProvider <.providers.AuthorisationProvider>`
i.e. |oauth1|_ or |oauth2|_ and we can access his/her **protected resources**.

.. literalinclude:: ../../examples/gae/simple/main.py
   :language: python
   :lines: 41

Each **provider** has it's specific API.
Let's first get the **user's** five most recent **Facebook** statuses.

.. literalinclude:: ../../examples/gae/simple/main.py
   :language: python
   :lines: 44, 46

Prepare the `Facebook Graph API <http://developers.facebook.com/docs/reference/api/>`_ URL.

.. literalinclude:: ../../examples/gae/simple/main.py
   :language: python
   :lines: 49, 50

Access the **user's** protected resource at that URL.

.. literalinclude:: ../../examples/gae/simple/main.py
   :language: python
   :lines: 53

Parse response.

.. literalinclude:: ../../examples/gae/simple/main.py
   :language: python
   :lines: 55, 57-73

Do the same with Twitter.

.. literalinclude:: ../../examples/gae/simple/main.py
   :language: python
   :lines: 75, 77-78, 80-81, 83-84, 86-101

That's it for the login handler.

Now just for convenience that we don't have to enter all the URLs manualy
let's create a *home* handler.

.. literalinclude:: ../../examples/gae/simple/main.py
   :language: python
   :lines: 105, 107

Create links to our *login* handler.

.. literalinclude:: ../../examples/gae/simple/main.py
   :language: python
   :lines: 110, 111

Create **OpenID** forms where the **user** can specify his/her **claimed ID**.
The library by default extracts the identifier from the query string ``id`` parameter,
but you can change its name to whatever you want.

.. literalinclude:: ../../examples/gae/simple/main.py
   :language: python
   :lines: 115-121, 123-128

Route URLs to your handlers.

.. literalinclude:: ../../examples/gae/simple/main.py
   :language: python
   :lines: 132, 133

Create the WSGI application.

.. literalinclude:: ../../examples/gae/simple/main.py
   :language: python
   :lines: 136

Finally, most important!!! Wrapp the app in :func:`authomatic.middleware`,
pass it the :doc:`reference/config` and some random secret string.

.. literalinclude:: ../../examples/gae/simple/main.py
   :language: python
   :lines: 139-

And here is the complete app:

.. literalinclude:: ../../examples/gae/simple/main.py

Don't forget to set up the ``app.yaml`` file.

.. literalinclude:: ../../examples/gae/simple/app.yaml