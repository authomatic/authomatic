Adapters
--------

The Authomatic library is based on processing HTTP request, serving HTTP responses, url fetches,
session management and database access.
Most of which functionality is available in allmost all Python web frameworks.

Adapters just unify different interfaces to this functionality across frameworks.

When using this library you only need to choose an adapter for your framework and
pass it's instance to the :func:`.authomatic.login` function.

.. note::
   
   Currently there is only the :class:`.gae.Webapp2Adapter` available.
   If you need an adapter for another framework your contributions are very welcome.
   Implementing an adapter is very easy for a framework expert.


.. automodule:: authomatic.adapters.gae
   :members:

.. automodule:: authomatic.adapters


