.. Authomatic documentation master file, created by
   sphinx-quickstart on Thu Feb  7 16:09:00 2013.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

Authomatic
==========

Bla

Usage
-----

Simple Example
^^^^^^^^^^^^^^

A simple example is worth a thousand words:

First create the :doc:`reference/config` dictionary:

.. literalinclude:: ../../examples/gae/simple/config-template.py

Create ``main.py`` file and mport what's needed.

.. literalinclude:: ../../examples/gae/simple/main.py
   :language: python
   :lines: 1-6

Create a simple request handler which accepts ``GET`` and ``POST`` HTTP methods and
recieves the ``provider_name`` URL variable. Don't write anything to response yet!

.. literalinclude:: ../../examples/gae/simple/main.py
   :language: python
   :lines: 10, 14
   
Inside the handler create an adapter for |webapp2|_ framework.

.. literalinclude:: ../../examples/gae/simple/main.py
   :language: python
   :lines: 17
   
Login the user with :func:`.authomatic.login`.

.. literalinclude:: ../../examples/gae/simple/main.py
   :language: python
   :lines: 20
   
The login procedure is finished when there is
the :class:`LoginResult <.core.LoginResult>`.
Now you can write to response.

.. literalinclude:: ../../examples/gae/simple/main.py
   :language: python
   :lines: 24, 28
   
Check for errors.

.. literalinclude:: ../../examples/gae/simple/main.py
   :language: python
   :lines: 30, 32
   
If there are no errors there must be a :class:`User <.core.User>` object.
We must update it if we need properties like **name** or **email**.  

.. literalinclude:: ../../examples/gae/simple/main.py
   :language: python
   :lines: 34, 39
   
Welcome the user.  

.. literalinclude:: ../../examples/gae/simple/main.py
   :language: python
   :lines: 42-44

We are done, but we can do more!

If there are :class:`credentials <.core.Credentials>` the user has logged in with an
:class:`AuthorisationProvider <.providers.AuthorisationProvider>`
i.e. |oauth1|_ or |oauth2|_ and we can access his/her **protected resources**.

.. literalinclude:: ../../examples/gae/simple/main.py
   :language: python
   :lines: 50

Each provider has it's specific API. First we do som tricks with Facebook.

.. literalinclude:: ../../examples/gae/simple/main.py
   :language: python
   :lines: 53, 55

Let's write something on the **users** timeline.
To be able to do it we must include the ``'publish_stream'`` scope in the config.

.. literalinclude:: ../../examples/gae/simple/main.py
   :language: python
   :lines: 58, 61, 64

To be sure that everything went right we can check the response.

.. literalinclude:: ../../examples/gae/simple/main.py
   :language: python
   :lines: 67-69, 71-77  

Do the same for Twitter.

.. literalinclude:: ../../examples/gae/simple/main.py
   :language: python
   :lines: 79, 81-82, 84, 88, 91-92, 94-96, 98-103

That's it for the login handler.

Now just for convenience that we don't have to enter all the URLs manualy
let's create a **home** handler.

.. literalinclude:: ../../examples/gae/simple/main.py
   :language: python
   :lines: 107, 109

Create links to login handler.

.. literalinclude:: ../../examples/gae/simple/main.py
   :language: python
   :lines: 112, 113

Create **OpenID** forms where the user can specify his/her **claimed ID**.
The library by default extracts the identifier from the query string ``id`` parameter,
but you can change its name to whatever you want.

.. literalinclude:: ../../examples/gae/simple/main.py
   :language: python
   :lines: 117-123, 125-130

Finally route URLs to your handlers...

.. literalinclude:: ../../examples/gae/simple/main.py
   :language: python
   :lines: 134, 135

...and instantiate the WSGI application.

.. literalinclude:: ../../examples/gae/simple/main.py
   :language: python
   :lines: 138

And here is the complete app:

.. literalinclude:: ../../examples/gae/simple/main.py

Don't forget to set up the ``app.yaml`` file.

.. literalinclude:: ../../examples/gae/simple/app.yaml

Advanced
^^^^^^^^

Bla

Credentials
"""""""""""

Bla

Asynchronous Requests
"""""""""""""""""""""

Bla


Reference:
----------

.. toctree::
   :maxdepth: 6
   
   reference/index