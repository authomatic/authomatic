JavaScript
----------

There is the ``authomatic.js`` library available with a tiny interface which makes your life even easier.

.. warning::
   
   The library is dependent on |jquery|!


.. js:function:: authomatic.setup(options)
   
   Sets up all the library's options.
   
   :param object options:
      An object of following options:
      
      
      .. js:attribute:: options.logging
         
         :js:data:`bool` If ``true`` the library will log a lot of information to the console.
      
      
      Popup options:
      
      .. js:attribute:: options.popupWidth
         
         :js:data:`int` The width of the popup in pixels. Default is ``800``.
      
      .. js:attribute:: options.pupupHeight
         
         :js:data:`int` The height of the popup in pixels. Default is ``600``.
      
      .. js:attribute:: options.popupLinkSelector
         
         :js:data:`string` A |jquery| selector specifying links that should be affected by
         :js:func:`.authomatic.popupInit`. Default is ``'a.authomatic'``.
      
      .. js:attribute:: options.popupFormSelector
         
         :js:data:`string` A |jquery| selector specifying forms that should be affected by
         :js:func:`.authomatic.popupInit`. Default is ``'form.authomatic'``.
      
      .. js:attribute:: options.popupFormValidator
         
         :js:data:`function` A function which you can use to validate the form before the popup opens.
         It accepts the |jquery| selected form. The popup gets opened only if it returns ``true``. 
      
      
      Callbacks:
      
      .. js:attribute:: options.onPopupInvalid
         
         :js:data:`function` Called when the popup form doesn't pass validation.
         Accepts the form selected with |jquery| as the only argument.
      
      .. js:attribute:: options.onPopupOpen
         
         :js:data:`function` Called when the popup gets open.
         Accepts the popup location URL as the only argument.
      
      .. js:attribute:: options.onLoginComplete
         
         :js:data:`function` Called when the popup gets closed after the login procedure is complete.
         Accepts the :js:data:`.loginResult` object as the only argument.
            

.. js:function:: authomatic.popupInit
   
   If you call this function, all ``<a></a>`` and ``<form></form>`` elements with ``class="authomatic"``
   will open a popup on click/submit. By links the location of the popup will be the value of ``href`` attribute,
   by forms the value of ``action`` attribute with query string extracted from the form inputs.
   
   .. code-block:: html
      
      <!DOCTYPE html>
      <html>
         <head>
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
               authomatic.popupInit();
            </script>
            
         </body>
      </html>

.. js:function:: authomatic.access(credentials, url[, options])
   
   Makes an asynchronous request to **protected resource** of a **user**.
   
   Under the hood it tries to make the request as efficiently as possible
   with the aim to save your backend's resources:
   
   *  By |oauth2|_ providers:
   
      #. First a *crosss-domain* XHR request is attempted.
      #. If that fails it continues either with:
      
         *  A *JSONP* XHR request but only if the provider supports it and the request method is ``'GET'``
         *  Otherwise it will fetch the provider through backend.
         
   *  By |oauth1|_ providers the request must be signed using the **consumer secret** which cannot
      be exposed in the client, so every request goes first to the backend.
      Depending on provider the backend either:
      
      *  Fetches the provider and returns the result of the fetch.
      *  Returns signed *request elements* with which a *JSONP* XHR request is made.
   
   :param string credentials:
      Serialized :class:`.Credentials` of the **user**.
   
   :param string url:
      URL of the **protected resource**. Can include querystring and template tags in the form of
      ``https://example.com/api/{user.id}/profile``.
   
   :param object options:
      An object of following options.
      
      .. note::
         
         You can also specify all of these options in the :js:func:`.authomatic.setup`.
         Values specified here will override the values specified in :js:func:`.authomatic.setup`
         with the exception of callbacks.
      
      .. js:attribute:: options.backend
         
         :js:data:`string` URL of your *login handler*, or the handler where you call the
         :func:`authomatic.json_endpoint` function.
         
         .. warning::
            
            This parameter is required by all |oauth1| providers
            and also by some |oauth2| providers.
      
      .. js:attribute:: options.forceBackend
         
         :js:data:`bool` If `true` requests will be fetched through backend by all **providers**.
      
      .. js:attribute:: options.substitute
         
         :js:data:`object` An object which will be used to replace template tags inside the :js:data:`URL`.
         e.g. URL ``https://example.com/api/{user.id}/profile`` by substitute ``{user: {id: '123'}}``
         will be rendered as ``https://example.com/api/123/profile``.
      
      .. js:attribute:: options.params
         
         :js:data:`object` The query parameters of the request.
      
      .. js:attribute:: options.headers
         
         :js:data:`object` The HTTP headers of the request.
      
      .. js:attribute:: options.body
         
         :js:data:`string` The body of the request.
      
      .. js:attribute:: options.jsonpCallbackPrefix
         
         :js:data:`string` Some providers don't support cross-domain requests.
         In such case the function tries a *JSONP* request and will generate a temporary callback
         in the global namespace with the name ``'authomaticJsonpCallback#'`` where ``#`` is an
         integer unique for every callback. You can change the default ``'authomaticJsonpCallback'``
         to whatever you want by specifying it in this option.
         
      Callbacks:
      
      .. warning::
         
         Callbacks specified in :js:func:`.authomatic.setup` will not be overriden by
         those specified here, but both will be called, whereas those specified in
         :js:func:`.authomatic.setup` will be called first.
      
      .. js:attribute:: options.onBackendStart
         
         :js:data:`function` Called when :js:func:`.authomatic.access` contacts backend.
         Accepts a object of parameters which will be sent to the backend as the only argument.
      
      .. js:attribute:: options.onBackendComplete
         
         :js:data:`function` Called when response returns from backend.
         Accepts ``data``, ``textStatus`` and ``jqXHR`` as arguments in the specified order.
      
      .. js:attribute:: options.onAccessSuccess
         
         :js:data:`function` Called when a successfull response returns from **provider**.
         Accepts ``data``, ``textStatus`` and ``jqXHR`` as arguments in the specified order.
      
      .. js:attribute:: options.onAccessComplete
         
         :js:data:`function` Called when any response returns from **provider**.
         Accepts ``textStatus`` and ``jqXHR`` as arguments in the specified order.







