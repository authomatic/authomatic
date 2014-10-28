|oauth2| Provider Implementation Tutorial
-----------------------------------------

Activate the virtual environment ``./venv``.

.. code-block:: bash

    $ . ./venv/bin/activate

Add the new provider to functional tests
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Change directory to ``./tests/functional_tests/``.

.. code-block:: bash

    $(venv) cd ./tests/functional_tests/

Create the *expected values* module for the new provider by copying the
``tests/functional_tests/expected_values/new_provider.py.template`` file to
``tests/functional_tests/expected_values/eventbrite.py``.

.. code-block:: bash

    $(venv) cp expected_values/new_provider.py.template expected_values/eventbrite.py

Create the functional tests config from the template
``tests/functional_tests/config-template.py``.

.. code-block:: bash

    $(venv) cp config-template.py config.py

Add a new provider slug to the ``INCLUDE_PROVIDERS`` list in the config in
correct alphabetical order and comment out all the other providers.

.. code-block:: python

    # tests/functional_tests/config.py

    # Only providers included here will be tested.
    # This is a convenience to easily exclude providers from tests by commenting
    # them out.
    INCLUDE_PROVIDERS = [
        # 'behance',
        # 'bitly',
        # 'deviantart',
        'eventbrite',
        # 'facebook',
        # 'foursquare',
        # 'google',
        # 'github',
        # 'linkedin',
        # 'paypal',
        # 'reddit',
        # 'vk',
        # 'windowslive',
        # 'yammer',
        # 'yandex',
    ]

Run the test. Make sure that you have the virtual environment active.

.. code-block:: bash

    $(venv) py.test -vv

The test should fail with the
``No record for the provider "provider_slug" was not found in the config!``
exception. Replace the ``'provider_slug'`` value on line 7 with the slug of the
new provider.

.. code-block:: python

    # tests/functional_tests/expected_values/eventbrite.py

    # (...)

    conf = fixtures.get_configuration('eventbrite')

Run the test again.

.. code-block:: bash

    $(venv) py.test -vv

It should fail again, this time with this exception:
``No record for the provider "eventbrite" was not found in the config!``.
We need to add a record for the new provider to the actual config dictionary.







#. Register by the provider and fill out ALL possible user profile fields.
#. Register an |oauth2| application by the provider.
#. Find the |oauth2| flow and user info endpoints in the provider's API documentation.
#. Make a domain alias for localhost.
#. Launch the ``./examples/flask/functional_test`` application.
#. Create a new class for the provider.
#. Override the |oauth2| enpoints.
#. Add the provider to functional tests.
  #. Add an entry to the functional tests config.
  #. Comment out all other providers in the ``INCLUDE_PROVIDERS`` list.
    #. Refresh the functional tests app and click on the link of the new provider.
        #. On the consent page open the browser inspector and copy the login,
           password and consent button(s) xpaths to the expected values file.
        #. If there was a problem debug, identify the problem and handle it in the
           ``_x_credentials_parser()`` method.
        #. If everything went good there should be a syntax highlighted json response.
        #. If the json response has any properties which were not automatically parsed
           to the user object you need to override the ``_x_user_parser()`` method.
  #. Stop the functional tests app.
  #. Run ``py.test -vv tests/functional_tests``
  #. A Firefox window should open and the tests should fill out the consent form
     and hit the consent button.
#. Add the provider's |oauth2|, API and app dashboard links if any to the
   docstring.