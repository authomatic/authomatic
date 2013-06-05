Simple |flask| Example 
----------------------

In this tutorial we will create a simple |flask|_ application
which will use **Authomatic** with :class:`.WerkzeugAdapter`
to log **users** in with Facebook, Twitter and |openid|_
and retrieve their recent tweets/statuses.

First create the :doc:`/reference/config` dictionary:

.. literalinclude:: ../../../examples/flask/werkzeug_adapter/config-template.py

Create ``main.py`` file and import what's needed.

.. literalinclude:: ../../../examples/flask/werkzeug_adapter/main.py
   :language: python
   :lines: 6-10

Create the *home* request handler.

.. literalinclude:: ../../../examples/flask/werkzeug_adapter/main.py
   :language: python
   :lines: 18-19, 24

Create the *login* request handler which should receive the ``provider_name`` URL variable and
should also accept the ``POST`` HTTP method to work properly with the :class:`.openid.OpenID`
provider which we have configured in the :doc:`/reference/config`.

.. literalinclude:: ../../../examples/flask/werkzeug_adapter/main.py
   :language: python
   :lines: 27-28

Now just Log the **user** in by calling the :meth:`.Authomatic.login` method inside the *login* handler.
You must pass it the :class:`.WerkzeugAdapter`
and the ``provider_name`` URL variable.
The :class:`.WerkzeugAdapter` needs |flask|_ ``request`` and ``response`` objects.
The handler must return the ``response`` so we assign it to a variable.

.. literalinclude:: ../../../examples/flask/werkzeug_adapter/main.py
   :language: python
   :lines: 34, 37

Now check whether there is a :class:`.LoginResult`.
If so, we need to update the :class:`.User` to get **his/her** info.
Then just pass the whole :class:`.LoginResult` to the template.

.. literalinclude:: ../../../examples/flask/werkzeug_adapter/main.py
   :language: python
   :lines: 40-41, 43, 46

If there is no :class:`.LoginResult` the *login procedure* is still pending and
we need to return the ``response``.

.. literalinclude:: ../../../examples/flask/werkzeug_adapter/main.py
   :language: python
   :lines: 49

Finally run the WSGI application.

.. literalinclude:: ../../../examples/flask/werkzeug_adapter/main.py
   :language: python
   :lines: 53-54

The rest happens in the templates.

First create a base template.

.. literalinclude:: ../../../examples/flask/werkzeug_adapter/templates/base.html
   :language: html+jinja

The ``index.html`` template contains just links to the *login* handler and
an OpenID form. The :meth:`.Authomatic.login` method expects the **claimed ID** to be in the
``id`` request parameter. This off course can be changed.

.. literalinclude:: ../../../examples/flask/werkzeug_adapter/templates/index.html
   :language: html+jinja

The most interesting things happen in the ``login.html`` template.
First create a link to the *home* handler.

.. literalinclude:: ../../../examples/flask/werkzeug_adapter/templates/login.html
   :language: html+jinja
   :lines: 1-2, 4, 6

Then check for possible errors.

.. literalinclude:: ../../../examples/flask/werkzeug_adapter/templates/login.html
   :language: html+jinja
   :lines: 9-11

And welcome the **user**.

.. literalinclude:: ../../../examples/flask/werkzeug_adapter/templates/login.html
   :language: html+jinja
   :lines: 14-18

Seems like we’re done, but we can do more.

If the **user** has :class:`.Credentials`, we can access **his/her protected resources**.

.. literalinclude:: ../../../examples/flask/werkzeug_adapter/templates/login.html
   :language: html+jinja
   :lines: 21

Let’s get the **user’s** five most recent Facebook statuses first.

.. literalinclude:: ../../../examples/flask/werkzeug_adapter/templates/login.html
   :language: html+jinja
   :lines: 24-25

Prepare the Facebook API URL.

.. literalinclude:: ../../../examples/flask/werkzeug_adapter/templates/login.html
   :language: html+jinja
   :lines: 28

And access the protected resource at that URL. The call returns a :class:`.Response` instance.

.. literalinclude:: ../../../examples/flask/werkzeug_adapter/templates/login.html
   :language: html+jinja
   :lines: 29

Check whether the response was successfull.

.. literalinclude:: ../../../examples/flask/werkzeug_adapter/templates/login.html
   :language: html+jinja
   :lines: 32

Parse the :attr:`.Response.data` attribute which is a data structure (:class:`dict` or :class:`list`)
parsed from the :attr:`.Response.content` which usually is **JSON**.

Handle possible errors.

.. literalinclude:: ../../../examples/flask/werkzeug_adapter/templates/login.html
   :language: html+jinja
   :lines: 34-36

If there are no errors, there should be a :class:`list` of statuses in the ``response.data.feed.data`` node.

.. literalinclude:: ../../../examples/flask/werkzeug_adapter/templates/login.html
   :language: html+jinja
   :lines: 38-39, 41-45

Close the opened ``{% if %}`` tags.

.. literalinclude:: ../../../examples/flask/werkzeug_adapter/templates/login.html
   :language: html+jinja
   :lines: 47, 49

Do the same for Twitter.

.. literalinclude:: ../../../examples/flask/werkzeug_adapter/templates/login.html
   :language: html+jinja
   :lines: 52-53, 55-56, 58, 60-62, 64-65, 64-71, 73, 75

Close the opened ``{% if result.user.credentials %}`` tag and the ``body`` block.

.. literalinclude:: ../../../examples/flask/werkzeug_adapter/templates/login.html
   :language: html+jinja
   :lines: 76, 78

Here is the complete ``login.html`` template.

.. literalinclude:: ../../../examples/flask/werkzeug_adapter/templates/login.html
   :language: html+jinja

And here the whole ``main.py`` module.

.. literalinclude:: ../../../examples/flask/werkzeug_adapter/main.py
   :language: python

That's it. Now just run the application.

.. code-block:: bash
   
   $ python main.py
