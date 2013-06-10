.. Authomatic documentation master file, created by
   sphinx-quickstart on Thu Feb  7 16:09:00 2013.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

.. toctree::
   :hidden:
   
   reference/index
   examples/index

Features
========

.. include:: ../../README.rst
   :start-line: 33
   :end-line: 80

.. contents::
   :backlinks: none

Usage
=====

So you want your app to be able to log a **user** in with **Facebook**, **Twitter**, |openid|_ or whatever?
First install **Authomatic** through `PyPi <https://pypi.python.org/pypi/Authomatic>`_,

.. code-block:: bash
   
   $ pip install authomatic

or clone it from `GitHub <http://github.com/peterhudec/authomatic>`_.

.. code-block:: bash
   
   $ git clone git://github.com/peterhudec/authomatic.git

.. note::
   
   On |gae|_ you need to include the :mod:`authomatic` module
   or a link to it inside your app's directory.

Now it's dead simple (hence the *Deadsimpleauth*). Just go through these two steps:

#. Make an instance of the :class:`.Authomatic` class.
#. Log the **user** in by calling the :meth:`.Authomatic.login` method inside a *request handler*.

.. note::
   
   The interface of the library has recently been changed from:

   .. code-block:: python

      import authomatic
      authomatic.setup(CONFIG, 'secret')

   to more flexible:

   .. code-block:: python

      from authomatic import Authomatic
      authomatic = Authomatic(CONFIG, 'secret')

   The old interface will be availabe up to version **0.1.0**,
   but you will recieve deprecation warnings in the log.

If everything goes good, you will get a :class:`.User` object with information like
:attr:`.User.name`, :attr:`.User.id` or :attr:`.User.email`.
Moreover, if the **user** has logged in with an |oauth2|_ or |oauth1|_ provider,
you will be able to access **his/her protected resources**.

Instantiate Authomatic
----------------------

You need to pass a :doc:`reference/config` dictionary and a random secret string
used for session signing and CSRF token generation to the constructor of the :class:`.Authomatic` class.

.. literalinclude:: ../../examples/gae/simple/main.py
   :lines: 1-8, 10
   :emphasize-lines: 9

The :doc:`reference/config` is a dictionary in which you configure
:doc:`reference/providers` you want to use in your app.
The keys are your internal **provider** names and
values are dictionaries specifying configuration for a particular **provider** name.

Choose a particular provider by assigning a |provider-class|_ to the ``"class_"`` key of
the nested *configuration dictionary*. All the other keys are just keyword arguments,
which will be passed to the chosen |provider-class|_ constructor.

In this sample *config* we specify that Facebook will be available under the ``"fb"`` slug,
Twitter under ``"tw"``, |openid| under ``"oi"`` and |gae| |openid| under ``"gae_oi"``:

.. literalinclude:: ../../examples/gae/simple/config-template.py

Log the User In
---------------

Now you can log the **user** in by calling the :func:`authomatic.login` function inside a *request handler*.
The *request handler* MUST be able to recieve both ``GET`` and ``POST`` HTTP methods.
You need to pass it an :doc:`adapter <reference/adapters>` for your framework
and one of the provider names which you specified in the keys of your :doc:`reference/config`.
We will get the provider name from the URL slug.

.. literalinclude:: ../../examples/gae/simple/main.py
   :lines: 13, 17, 20
   :emphasize-lines: 3

The :func:`authomatic.login` function will redirect the **user** to the **provider**,
which will prompt **him/her** to authorize your app (**the consumer**) to access **his/her**
protected resources (|oauth1|_ and |oauth2|_), or to verify **his/her** claimed ID (|openid|_).
The **provider** then redirects the **user** back to *this request handler*.

If the *login procedure* is over, :func:`authomatic.login` returns a :class:`.LoginResult`.
You can check for errors in :attr:`.LoginResult.error`
or in better case for a :class:`.User` in :attr:`.LoginResult.user`.
The :class:`.User` object has plenty of useful properties.

.. warning::
   
   Do not write anything to the response unless the *login procedure* is over!
   The :func:`authomatic.login` either returns ``None``,
   which means that the *login procedure* si still pending,
   or a :class:`.LoginResult` which means that the *login procedure* is over.

Check whether *login procedure* is over.

.. literalinclude:: ../../examples/gae/simple/main.py
   :lines: 23, 25

Check for errors, but hope that there is a :attr:`.LoginResult.user`.
If so, we have an authenticated **user** logged in.
Before we print a welcoming message we need to update the :class:`.User`
to get more info about **him/her**.
 
.. literalinclude:: ../../examples/gae/simple/main.py
   :lines: 27, 29, 31, 36-37, 40-42

Advanced
--------

Logging a **user** in is nice, but you can do more.

You can use the **user's** credentials_ to **access his/her protected resources**,
make `asynchronous requests`_, use your own session_ implementation and
Save your backend's resources by utilizing the :doc:`authomatic.js <reference/javascript>`
javascript_ library.


Credentials
^^^^^^^^^^^

If the :class:`.User` has :attr:`.User.credentials`,
**he/she** is logged in either with |oauth1|_ or |oauth2|_,
both of which are subclasses of :class:`.AuthorizationProvider`.
That means, that we can access the **user's protected resources**.
Lets get the **user's** five most recent facebook statuses.

.. literalinclude:: ../../examples/gae/simple/main.py
   :lines: 48, 51-52, 55-56, 59
   :emphasize-lines: 6

The call returns a :class:`.Response` object. The :attr:`.Response.data` contains the parsed
response content.

.. literalinclude:: ../../examples/gae/simple/main.py
   :lines: 61, 63-79

Credentials can be serialized to a lightweight url-safe string.

::
   
   serialized_credentials = credentials.serialize()

It would be useless if they could not be deserialized back to original.

.. note::
   
   The deserialization of the credentials is dependent on the :doc:`reference/config`
   used when the credentials have been serialized.
   You can deserialize them in a different application as long as you use the same :doc:`reference/config`.

::
   
   credentials = authomatic.credentials(serialized_credentials)

They know the provider name which you specified in the :doc:`reference/config`.

::
   
   provider_name = credentials.provider_name

|oauth2|_ credentials have limited lifetime. You can check whether they are still valid,
in how many seconds they expire, get the date and time or UNIX timestamp of their expiration
and find out whether they expire soon.

::
   
   valid = credentials.valid # True / False
   seconds_remaining = credentials.expire_in
   expire_on = credentials.expiration_date # datetime.datetime()
   expire_on = credentials.expiration_time # 1362080855
   should_refresh = credentials.expire_soon(60 * 60 * 24) # True if expire in less than one day

You can refresh the credentials while they are still valid.
Otherwise you must repeat the :func:`authomatic.login` procedure to get new credentials.

::
   
   if credentials.expire_soon():
      response = credentials.refresh()
      if response and response.status == 200:
         print 'Credentials have been refreshed successfully.'

Finally use the credentials (serialized or deserialized) to access **protected resources** of the **user**
to whom they belong by passing them to the :func:`authomatic.access` function along with the **resource** URL.

::
   
   response = authomatic.access(credentials, 'https://graph.facebook.com/{id}?fields=birthday')

You can find out more about :class:`.Credentials` in the :doc:`reference/index`.
There is also a short :doc:`tutorial about credentials <examples/credentials>`
in the :doc:`examples/index` section.

Asynchronous Requests
^^^^^^^^^^^^^^^^^^^^^

Following functions fetch remote URLs and
block the current thread till they return a :class:`.Response`.

* :func:`.authomatic.access`
* :meth:`.AuthorizationProvider.access`
* :meth:`.User.update`
* :meth:`.Credentials.refresh`

If you need to call more than one of them in a single *request handler*,
or if there is another **time consuming** task you need to do,
there is an **asynchronous** alternative to each of these functions.

* :func:`.authomatic.async_access`
* :meth:`.AuthorizationProvider.async_access`
* :meth:`.User.async_update`
* :meth:`.Credentials.async_refresh`

.. warning:: |async|

These **asynchronous** alternatives all return a :class:`.Future` instance which
represents the separate thread in which their **synchronous** brethren are running.
You should call all the **asynchronous** functions you want to use at once,
then do your **time consuming** tasks and finally collect the results of the functions
by calling the :meth:`get_result() <.Future.get_result>` method of each of the
:class:`.Future` instances.

::
   
   # These guys will run in parallel and each returns immediately.
   user_future = user.async_update()
   credentials_future = user.credentials.async_refresh()
   foo_future = authomatic.access(user.credentials, 'http://api.example.com/foo')
   bar_future = authomatic.access(user.credentials, 'http://api.example.com/bar')
   
   # Do your time consuming task.
   time.sleep(5)
   
   # Collect results:
   
   # Updates the User instance in place and returns response.
   user_response = user_future.get_result()
   if user_response.status == 200:
      print 'User was updated successfully.'
   
   # Refreshes the Credentials instance in place and returns response.
   credentials_response = credentials_future.get_result()
   if credentials_response.status == 200:
      print 'Credentials were refreshed successfully.'
   
   foo_response = foo_future.get_result()
   bar_response = bar_future.get_result()

   

Session
^^^^^^^

The :func:`authomatic.login` function uses a default **secure cookie** based session
to store state during the *login procedure*.
If you want to use different session implementation you can pass it
together with its **save method** to the :func:`authomatic.login` function.
The only requirement is that the session implementation must have a dictionary-like interface.

.. note::
   
   The default **secure cookie** based session will be deleted immediately after
   the *login procedure* is over. Custom sessions however, will be preserved.

::
   
   import webapp2
   from webapp2_extras import sessions
   import authomatic
   from authomatic.adapters import Webapp2Adapter
   
   class Login(webapp2.RequestHandler):
      def any(self, provider_name):
         
         # Webapp2 session
         session_store = sessions.get_store(request=self.request)
         session = session_store.get_session()
         session_saver = lambda: session_store.save_sessions(self.response)
         
         result = authomatic.login(Webapp2Adapter(self),
                                   provider_name,
                                   session=session,
                                   session_saver=session_saver)

Man, isn't there a simpler way to make a |webapp2| session?
You guessed it didn't you? There is one in the :mod:`authomatic.extras.gae` module:

::
   
   import webapp2
   import authomatic
   from authomatic.adapters import Webapp2Adapter
   from authomatic.extras import gae
   
   class Login(webapp2.RequestHandler):
      def any(self, provider_name):
         
         # Creates a new Webapp2 session.
         session = gae.Webapp2Session(self, secret='your-super-confidential-secret')
         
         result = authomatic.login(Webapp2Adapter(self),
                                   provider_name,
                                   session=session,
                                   session_saver=session.save)

If you are already using a |webapp2| session you can do it like this: 

::
   
   import webapp2
   import authomatic
   from authomatic.adapters import Webapp2Adapter
   from authomatic.extras import gae
   
   class Login(webapp2.RequestHandler):
      def any(self, provider_name):
         
         # Wraps an existing Webapp2 session.
         session = gae.Webapp2Session(self, session=self.session)
         
         result = authomatic.login(Webapp2Adapter(self),
                                   provider_name,
                                   session=session,
                                   session_saver=session.save)

JavaScript
^^^^^^^^^^

Popup
"""""

The :func:`authomatic.login` function redirects the **user** to the **provider**
to ask him for **his/her** consent. If you rather want to make the redirect in a popup,
the :ref:`authomatic.popupInit() <js_popup_init>` function of the
:ref:`javascript.js <js>` library with conjunction with :meth:`.LoginResult.js_callback`
make it a breeze.

Just add the ``authomatic`` class to your *login handler* links and forms
and change their default behavior by calling the :ref:`authomatic.popupInit() <js_popup_init>` function.
The elements will now open a 600 x 800 centered popup on click or submit respectively.
you can change the popup dimensions with the :ref:`authomatic.setup() <js_setup>`.

Set the ``onLoginComplete`` event handler to the :ref:`authomatic.setup() <js_setup>` function,
which should accept a ``result`` argument.

.. code-block:: html


   <!DOCTYPE html>
   <html>
      <head>

         <title>Login Popup Example<title>

         <!-- authomatic.js is dependent on jQuery -->
         <script type="text/javascript" src="http://code.jquery.com/jquery-1.9.1.min.js"></script>
         <script type="text/javascript" src="authomatic.js"></script>

      </head>
      <body>
         
         <!-- Opens a popup with location = "login/facebook" -->
         <a class="authomatic" href="login/facebook">Login with Facebook</a>
         
         <!-- Opens a popup with location = "login/openid?id=me.yahoo.com" -->
         <form class="authomatic" action="login/openid" method="GET">
            <input type="text" name="id" value="me.yahoo.com" />
            <input type="submit" value="Login with OpenID" />
         </form>
         
         <script type="text/javascript">

            // Set up the library
            authomatic.setup({
               popupWidth: 600,
               popupHeight: 400,
               onLoginComplete: function(result) {
                  // Handle the login result when the popup closes.
                  if (result.user) {
                     alert('Hi ' + result.user.name);
                  } else if (result.error) {
                     alert('Error occurred: ' + result.error.message);
                  }
               }
            });

            // Change behavior of links and form of class="authomatic"
            authomatic.popupInit();

         </script>
         
      </body>
   </html>

In your *login handler* just write the return value of the :meth:`.LoginResult.js_callback` method
to the response.

.. code-block:: python
   :emphasize-lines: 11
   
   import webapp2
   import authomatic
   from authomatic.adapters import Webapp2Adapter

   class Login(webapp2.RequestHandler):
       def any(self, provider_name):
           result = authomatic.login(Webapp2Adapter(self), provider_name)
           if result:
               if result.user:
                   result.user.update()
               self.response.write(result.js_callback())

The :meth:`.LoginResult.js_callback` generates a HTML that closes the popup when the *login procedure*
is over and triggers the ``onLoginComplete`` event handler with a JSON *login result* object passed as argument.
The *login result* object has similar structure as the :class:`.LoginResult`.

Access
""""""

Accessing the **user's protected resources** and **provider APIs** is very easy
thanks to the :func:`authomatic.access` function, but you could save your backend's resources
by delegating it to the **user's** browser.
   
This however is easier said then done because some **providers** do not support
*cross-domain* and *JSONP* requests and all |oauth1|_ request need to be signed
with the **consumer secret** by the backend.
Leave alone special request requirements invented by some zealous providers
on top of the |oauth1|_ and |oauth2|_ standards.

The :ref:`authomatic.access() <js_access>` function of the :ref:`javascript.js <js>` library
solves this for you. It encapsulates solutions of all the aforementioned issues and
always makes the request in the most efficient way.

.. code-block:: javascript
   
   authomatic.access(loginResult.user.credentials, 'https://graph.facebook.com/{id}/feed',{
      substitute: loginResult.user, // replaces the {id} in the URL with loginResult.user.id.
      onAccessSuccess: function(data) {
         alert('Your most recent status is: ' + data.data[0].story);
      },
      onAccessComplete: function(textStatus) {
         if (textStatus == 'error') {
            alert('We were unable to get your Facebook feed!');
         }
      }
   });
