|oauth2| Provider Implementation Tutorial
-----------------------------------------


#. Copy the expected values template.
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