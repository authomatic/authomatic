.. Authomatic documentation master file, created by
   sphinx-quickstart on Thu Feb  7 16:09:00 2013.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

.. toctree::
   :hidden:
   
   self
   reference/index
   examples/index



Usage
=====

It's very simple. You only need to do these three steps to have the **user** logged in:

* Configure **providers** that you want to use in the :doc:`/reference/config` dictionary.
* Wrap your WSGI app in the :func:`.authomatic.middleware`.
* Call the :func:`.authomatic.login` function inside a *request handler*.

If everything goes good, you will get a :class:`.User` object with informations like
:attr:`.User.name`, :attr:`.User.id` or :attr:`.User.email`.
Moreover, if the **user** has logged in with an |oauth2|_ or |oauth1|_ provider,
you will be able to access **his/her protected resources**.

Create the Config
-----------------

The :doc:`reference/config` is a dictionary of **providers** you want to use in your app.
The keys are your internal **provider** names or slugs,
the values are dictionaries specifying configuration for a particular **provider** name.

Choose a particular provider by assigning a |provider-class|_ to the ``"class_"`` key of
the nested *configuration dictionary*. All the other keys are just keyword arguments,
which will be passed to the chosen |provider-class|_ constructor.

In this sample :doc:`reference/config` we specify that Facebook will be available under the ``"fb"`` slug,
Twitter under ``"tw"``, |openid| under ``"oi"`` and |gae| |openid| under ``"gae_oi"``:

.. literalinclude:: ../../examples/gae/simple/config-template.py

Wrap Your WSGI App In Middleware
--------------------------------

You add the **authorisation/authentication** capability to your WSGI app
by wrapping it in the :func:`authomatic.middleware`.
You need to pass it the original WSGI app, the :doc:`reference/config` and a random secret string.

::
   
   import webapp2
   from config import CONFIG
   
   ROUTES = [webapp2.Route(r'/login/<:.*>', 'Login', handler_method='any')]
   
   # Instantiate your framework's WSGI app.
   original_app = webapp2.WSGIApplication(ROUTES, debug=True)
   
   # Wrapp it in middleware.
   wrapped_app = authomatic.middleware(original_app, CONFIG, 'your-super-secret-string')

Call the Login Method
---------------------

Now you can log the **user** in by calling the :func:`authomatic.login` function inside a *request handler*.
The *request handler* MUST be able to recieve both ``GET`` and ``POST`` HTTP methods.
You need to pass it one of the provider names which you specified in the keys of your :doc:`reference/config`.
Wi will get it from the URL slug.

.. literalinclude:: ../../examples/gae/simple/main.py
   :lines: 3-4, 6, 8, 12, 16

The :func:`authomatic.login` function will redirect the **user** to the **provider**,
which will promt **him/her** to authorise your app (**the consumer**) to access **his/her**
protected resources (|oauth1| and |oauth2|), or to verify **his/her** claimed ID (|openid|).
The **provider** then redirect the **user** back to this *request handler*.

The :func:`authomatic.login` function returns a :class:`.LoginResult`.
If the *login procedure* is over there will be either a :attr:`.LoginResult.error`
or in better case a :attr:`.LoginResult.user`.
The :class:`.User` object has plenty of usefull properties.

.. literalinclude:: ../../examples/gae/simple/main.py
   :lines: 18, 20, 22, 26-27, 30-32

If there are :attr:`.User.credentials`, the **user** is logged in with |oauth1| or |oauth2|
and we can access **his/her protected resources**.

.. literalinclude:: ../../examples/gae/simple/main.py
   :lines: 46-47, 50

The call returns a :class:`.Response` object. The :attr:`.Response.data` contains the parsed
response content.

.. literalinclude:: ../../examples/gae/simple/main.py
   :lines: 52, 54-55, 57-67

Advanced
========

Apart from getting the **user** logged in you can use **his/her**
credentials_ to **access his/her protected resources**,
make `asynchronous requests`_ and use your own session_ implementation.


Credentials
-----------

If the **user** has logged in with an :class:`.AuthorisationProvider` i.e. |oauth1|_ or |oauth2|_,
the :attr:`.User.credentials` attribute will contain a :class:`.Credentials` object.

::
   
   if result.user.credentials:
      # User logged in with Oauth 2.0 or Oauth 1.0a
      credentials = result.user.credentials

Credentials can be serialized to a lightweight url-safe string.

::
   
   serialized = credentials.serialize()

It would be useles if they could not be deserialized back to original.

.. note::
   
   The deserialization of the credentials is dependent on the :doc:`reference/config`
   used when the credentials have been serialized.
   You can deserialize them in a different application as long as you wrapp it in the
   :func:`authomatic.middleware` with the same :doc:`reference/config`.

::
   
   credentials = authomatic.credentials(serialized)

They know the provider name which you specified in the :doc:`reference/config`.

::
   
   provider_name = credentials.provider_name

|oauth2| credentials have limited lifetime. You can check whether they are still valid,
in how many seconds they expire, get the date and time or UNIX timestamp of their expiration
and find out whether they expire soon.

::
   
   valid = credentials.valid # True / False
   seconds_remaining = credentials.expire_in
   expire_on = credentials.expiration_date # datetime.datetime()
   expire_on = credentials.expiration_time # 1362080855
   should_refresh = credentials.expire_soon(60 * 60 * 24) # True if expire in less than one day

You can refresh the credentials if they will expire soon.
If they are not valid anymore you must call the :func:`authomatic.login` function to get new credentials.

::
   
   if credentials.expire_soon():
      response = credentials.refresh()
      if response and response.status == 200:
         print 'Credentials have been refreshed succesfully.'

Finally use the credentials (serialized or deserialized) to access **protected resourcess** of the **user**
by passing it to the :func:`authomatic.access` function along with the **resource** URL.

::
   
   response = authomatic.access(credentials, 'https://graph.facebook.com/#####?fields=birthday')

Asynchronous Requests
---------------------

Following functions fetch remote URLs and
block the current thread till they return a :class:`.Response`.

* :func:`.authomatic.access`
* :meth:`.AuthorisationProvider.access`
* :meth:`.User.update`
* :meth:`.Credentials.refresh`

If you need to call more than one of them in a single *request handler*,
or if there is another **time consuming** task you need to do,
there is an **asynchronous** alternative to each of the functions.

* :func:`.authomatic.async_access`
* :meth:`.AuthorisationProvider.async_access`
* :meth:`.User.async_update`
* :meth:`.Credentials.async_refresh`

.. warning:: |async|

These **asynchronous** alternatives all return a :class:`.Future` instance which
represents the separate thread in which their **synchronous** brethrens are running.
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
-------

The library uses a default **secure cookie** based session to store state during the *login procedure*.
If you want to use another session implementation you can pass it
together with its **save method** to the :func:`authomatic.login` function.
The only requirement is that the session implementation must have a dictionary-like interface.

::
   
   import webapp2
   from webapp2_extras import sessions
   import authomatic
   
   class Login(webapp2.RequestHandler):
      def any(self, provider_name):
         
         # Webapp2 session
         session_store = sessions.get_store(request=self.request)
         session = session_store.get_session()
         session_saver = lambda: session_store.save_sessions(self.response)
         
         result = authomatic.login(provider_name,
                                   session=session,
                                   session_save_method=session_saver)

Man, isn't there a simpler way to make a |webapp2| session?
You guessed it didn't you? There is one in the :mod:`authomatic.extras.gae` module:

::
   
   import webapp2
   import authomatic
   from authomatic.extras import gae
   
   class Login(webapp2.RequestHandler):
      def any(self, provider_name):
         
         session = gae.Webapp2Session(self, 'your-super-confidential-secret')
         
         result = authomatic.login(provider_name,
                                   session=session,
                                   session_save_method=session.save)

If you are allready using a |webapp2| session you can do it like this: 

::
   
   import webapp2
   import authomatic
   from authomatic.extras import gae
   
   class Login(webapp2.RequestHandler):
      def any(self, provider_name):
         
         session = gae.Webapp2Session(self, self.session)
         
         result = authomatic.login(provider_name,
                                   session=session,
                                   session_save_method=session.save)


   
   
   
   