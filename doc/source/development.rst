Development
===========

Contributions are very welcome.
Please read this guide if you want to contribute.

Development Environment Setup
-----------------------------

Fork the
`Authomatic repository on Github <https://github.com/peterhudec/authomatic>`__
and clone it:

.. code-block:: bash

   $ git clone https://github.com/<your-github-id>/authomatic.git
   $ cd authomatic

.. note::

    The rest of this document assumes that you are working in the ``authomatic/`` directory.

Although Authomatic has no dependencies except for the optional
|pyopenid|_ package required by the :class:`.openid.OpenID` provider,
it has quite a lot of development dependencies.

The easiest way to set up the development environment is to run the
``./bootstrap.sh`` script.

.. code-block:: bash

   $ sh bootstrap.sh

The script does following things:

#. Initializes and updates GIT submodules. The
   `Foundation Sphinx Theme <https://github.com/peterhudec/foundation-sphinx-theme>`__
   located in ``./doc/source_/themes/foundation-sphinx-theme``
   is currently the only GIT submodule used.
#. Creates a `virtual environment <https://virtualenv.pypa.io/en/latest/>`__
   in ``./venv``.
#. Downloads and extracts the
   `Google App Engine Python SDK <https://developers.google.com/appengine/downloads#Google_App_Engine_SDK_for_Python>`__
   for **Linux/Other Platforms** to ``./venv/google_appengine``.
#. Downloads the `Chromedriver <https://code.google.com/p/chromedriver/>`__
   executable needed by selenium tests to ``./venv/bin/chromedriver``.
#. Activates the virtual environment ``./venv``.
#. Installs the development dependencies specified in ``./requirements.txt``.
#. Prepares the ``./doc/build/html`` directory for deployment of the compiled documentation to `Github Pages <https://pages.github.com/>`__.
    #. Removes the ``./doc/build/`` directory if it exists.
    #. Clones the origin of this repository to ``./doc/build/html``.
    #. Creates the **gh-pages** branch there.
    #. Sets the GIT **HEAD** to **gh-pages**.
    #. Removes the GIT index.
    #. Removes everything in the directory with ``git claen -fdx``.
#. Compiles the documentation.
#. Deactivates the virtual environment (probably unneccessary).

Documentation Compilation and Deployment
----------------------------------------

.. warning::

    Allways keep the documentation in sync with the latest code changes.

Compile the documentation with this commands:

.. code-block:: bash

   $ . ./venv/bin/activate
   (venv)$ cd doc
   (venv)$ make html

The documentation will be compiled to ``./doc/build/html``.
For easy deploiment to `Github Pages <https://pages.github.com/>`__,
the ``./doc/build/html`` directory is actually a clone of the **origin** of the
actual project repository that you cloned from (your fork) with the
**gh-pages** branch checked out.

To deploy a compiled documentation to Github page go to the
``./doc/build/html`` directory, commit all changes and push to
**origin gh-pages**:

.. code-block:: bash

    $ cd doc/build/html
    $ git add -A
    $ git commit -m "Updated documentation."
    $ git push origin gh-pages

Tests
-----

There are currently only *functional* (or *end-to-end*)
`Selenium <http://seleniumhq.org>`__ tests.
They are designed to test the *login procedure* and
*credentials refreshment* and to discover changes in provider APIs.
Currently the tests cover only 11 of the 27 |oauth2| providers.
The tests are written for the `pytest <http://pytest.org/latest/>`__ framework.

To run *functional* tests, you first need to create the
``./tests/functional_tests/config.py`` module by copying and filling out the
``./tests/functional_tests/config-template.py` template.

.. code-block:: bash

    $ cd tests/functional_tests
    $ cp config-template.py config.py

This is the ``config-template.py`` template:

.. literalinclude:: ../../tests/functional_tests/config-template.py

If you want to run tests for all of the 8 covered providers,
you should register an **application** and a **user account** by each of them
and fill out **all possible** settings in the user profile.
You can exclude providers from the tests by comenting them out of the
``INCLUDE_PROVIDERS`` list.

You should also add an alias for the IP address of your localhost, because
some providers like Twitter require the ``callback_uri``
to match a domain pattern.

.. code-block:: bash

    $ sudo echo -e "127.0.0.1\tauthomatic.com" >> /etc/hosts
    $ cat /etc/hosts
    # Host Database
    #
    # localhost is used to configure the loopback interface
    # when the system is booting.  Do not change this entry.
    ##
    127.0.0.1	localhost
    127.0.0.1	authomatic.com

You can run the tests with the following command
with the virtual environment activated:

.. code-block:: bash

    $ . venv/bin/activate
    (venv)$ py.test tests/functional_tests



