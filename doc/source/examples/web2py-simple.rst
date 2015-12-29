Simple |web2py| Example 
-----------------------

.. seo-description::
   
   A simple tutorial where we create a web2py app which can log users
   in with Facebook, Twitter and OpenID and read their recent statuses.

In this tutorial we will create a simple |web2py|_ application
that will be able to log **users** in with Facebook, Twitter and |openid|_
and retrieve their 5 most recent tweets/statuses.

You can download all the source files we are about to create
`here <https://github.com/peterhudec/authomatic/tree/master/examples/django>`__.

First download and start web2py, 

.. code-block:: bash

   $ wget http://web2py.com/examples/static/web2py_src.zip
   $ unzip web2py_src.zip
   $ cd web2py
   $ python web2py.py -a hello -p 8000 &
   $ open http://127.0.0.1/8000/admin

then create a new web2py application named *simple*

.. code-block:: bash

   $ mkdir applications/simple
   $ cp -r applications/welcome/* applications/simple

Now in the ``applications/simple/modules`` directory create the ``authomatic_config.py`` module
with the :doc:`/reference/config` dictionary where you set up all the providers you want to use.
You will need the ``consumer_key`` and ``consumer_secret`` which you can get
`here <https://developers.facebook.com/apps>`__ for Facebook and
`here <https://dev.twitter.com/apps>`__ for Twitter.

.. note::
   
   Facebook and other |oauth2| providers require a **redirect URI**
   which should be the URL of the *login view*
   which we will create in this tutorial and whose walue in our case will be
   ``http://[hostname]/simple/login/fb`` for Facebook.

.. code-block:: python

   from authomatic.providers import oauth2, oauth1, openid
   
   CONFIG = {
    
     'tw': { # Your internal provider name
        
        # Provider class
        'class_': oauth1.Twitter,
        
        # Twitter is an AuthorizationProvider so we need to set several other properties too:
        'consumer_key': '########################',
        'consumer_secret': '########################',
      },
    
      'fb': {
           
        'class_': oauth2.Facebook,
        
        # Facebook is an AuthorizationProvider too.
        'consumer_key': '########################',
        'consumer_secret': '########################',
        
        # But it is also an OAuth 2.0 provider and it needs scope.
        'scope': ['user_about_me', 'email', 'publish_stream'],
      },
    
      'oi': {
           
        # OpenID provider dependent on the python-openid package.
        'class_': openid.OpenID,
      }
   }

The rest happens in the ``applications/simple/default.py`` file. Here is the complete file:

.. code-block:: python

    def login():
        from authomatic import Authomatic
        from authomatic.adapters import Web2pyAdapter
        provider_name = request.args(0)
        authomatic = Authomatic(CONFIG, 'a super secret random string')
        result = authomatic.login(Web2pyAdapter(request, response), provider_name)
        if result.error:
            response.write('<h2>Damn that error: {0}</h2>'.format(result.error.message))
        elif result.user:
            if not (result.user.name and result.user.id):
               result.user.update()
            return "<h1>Hi {0} {1} {2}</h1>".format(result.user.name,
                                                    result.user.id,
                                                    result.user.email)
        return 'done'

In future versions of web2py, Authmatic will be ingrated with the buil-in Auth object.
Please look into the web2py documentation for this.