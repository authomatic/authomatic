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

The script does following:

#. Initializes and updates GIT submodules. The
   `Foundation Sphinx Theme <https://github.com/peterhudec/foundation-sphinx-theme>`__
   located in ``./doc/source_/themes/foundation-sphinx-theme``
   is currently the only GIT submodule used.
#. Creates a `virtual environment <https://virtualenv.pypa.io/en/latest/>`__
   ``./e``.
#. Installs the development dependencies specified in ``./requirements.txt``
   to the ``e`` virtual environment.
#. Runs the ``tox -r --notest`` command which creates virtual environments
   ``./.tox/py26``, ``./.tox/py27`` and ``./tox/py34``.
#. Creates symbolic links to ``./.tox/py27/lib/python2.7/site-packages/openid``
   and ``./authomatic`` in each of the ``./examples/gae/*`` directories.
#. Prepares the ``./doc/build/html`` directory for deployment of the compiled documentation to `Github Pages <https://pages.github.com/>`__.
    #. Removes the ``./doc/build/`` directory if it exists.
    #. Clones the origin of this repository to ``./doc/build/html``.
    #. Creates the **gh-pages** branch there.
    #. Sets the GIT **HEAD** to **gh-pages**.
    #. Removes the GIT index.
    #. Removes everything in the directory with ``git claen -fdx``.
#. Compiles the documentation with the ``./.tox/py27`` virtual environment
   activated.

PyOpenSSL Error
^^^^^^^^^^^^^^^

It is likely, that you will encounter some of following errors during
installation of the **pyopenssl** package:

Missing Python headers ``Python.h: No such file or directory``:

Fix it by installing Python development package e.g:

.. code-block:: bash

    $ sudo apt-get install python3.4-dev

Missing libffi headers ``ffi.h: No such file or directory``:

Fix it by installing libffi development package e.g:

.. code-block:: bash

    $ sudo apt-get install libffi-dev


Documentation Compilation and Deployment
----------------------------------------

.. warning::

    Always keep the documentation in sync with the latest code changes.

Compile the documentation with this commands:

.. code-block:: bash

   $ . ./.tox/py27/bin/activate
   (py27)$ cd doc
   (py27)$ make html

The documentation will be compiled to ``./doc/build/html``.
For easy deploiment to `Github Pages <https://pages.github.com/>`__,
the ``./doc/build/html`` directory is actually a clone of the **origin** of the
actual project repository that you cloned from (your fork) with the
**gh-pages** branch checked out.

To deploy a compiled documentation to GitHub page go to the
``./doc/build/html`` directory, commit all changes and push to
**origin gh-pages**:

.. code-block:: bash

    $ cd doc/build/html
    $ git add -A
    $ git commit -m "Updated documentation."
    $ git push origin gh-pages

Testing
-------

Tests are written in `pytest <http://pytest.org/>`__
and `Tox <https://testrun.org/tox>`__ is used to run them against
**Python 2.6**, **Python 2.7** and **Python 3.4**.


There are currently only *functional* (*end-to-end*)
`Selenium <http://seleniumhq.org>`__ tests.
They are designed to test the *login procedure* and
*credentials refreshment* and to discover changes in provider APIs.

To run *functional* tests, you first need to create the
``./tests/functional_tests/config.py`` module by copying and filling out the
``./tests/functional_tests/config-template.py`` template.

.. code-block:: bash

    $ cd tests/functional_tests
    $ cp config-template.py config.py

If you want to run tests for all of the covered providers,
you should register an **application** and a **user account** by each of them
and fill out **all possible** settings of the user profile.
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

Finally launch the tests:

.. code-block:: bash

    (e)$ tox

If you want **tox** to only run tests for let's say
**Python 2.6** and **Python 3.4** use the ``-e`` option:

.. code-block:: bash

    (e)$ tox -e py26, py34

If something goes wrong, you can examine the **py.test** logs, at
``./tests/pytest-pyXX.log`` and the provider login logs at
``./tests/functional_tests/login-pyXX.log``.

You can watch the login logs while the tests are running with the
``tail -f`` command. This is useful when debugging the login on Firefox on Linux
in an invisible display.

.. code-block:: bash

    $ tail -f ./tests/functional_tests/login-py*.log

Deployment to Travis CI
^^^^^^^^^^^^^^^^^^^^^^^

Register at `Travis CI <https://travis-ci.org/>`__ and configure your fork
of Authomatic (read the `getting started section
<http://docs.travis-ci.com/user/getting-started/>`__ if you don't know how).

Install the `Travis CI command line client
<https://github.com/travis-ci/travis.rb>`__.

.. code-block:: bash

    (e)$ sudo gem install travis

Log in.

.. code-block:: bash

    (e)$ travis login --org

Tweak the Travis CI specific settings in ``./tests/functional_tests/config.py``,
or better leave it as it is.

.. literalinclude:: ../../tests/functional_tests/config-template.py
   :language: python
   :lines: 92-108

.. note::

    **LinkedIn** and **WindowsLive** add a *captcha* to the user login form
    if the user tries to log in from an unusual location
    like the Travis CI servers in the US.

Encrypt the config and add it automatically to ``./.travis.yml``.

.. code-block:: bash

    (e)$ travis encrypt-file ./tests/functional_tests/config.py ./tests/functional_tests/config.py.enc --add

Commit the encrypted config and updated ``./.travis.yml`` and push it to GitHub.

.. code-block:: bash

    (e)$ git add ./.travis.yml ./tests/functional_tests/config.py.enc
    (e)$ git commit -m 'Updated Travis CI config.'
    (e)$ git push

Go to ``https://travis-ci.org/<your-github-username>/authomatic/builds/`` and
watch it pass (hopefully). If the tests fail, the
``./tests/functional_tests/login-py*.log`` and the
``./tests/pytest-py*.log`` logs will be displayed at the end of the log
so you can get a hang of what went wrong.

Running the Examples
--------------------

If you want to run any of the ``./examples/`` just copy the example's
``config-template.py`` to ``config.py``, fill it out,
activate one of the virtual environments in ``./tox/`` and run the example
the usual way according to its framework.

Example of launching the :doc:`examples/django-simple` with Python 3.4:

.. code-block:: bash

    $ . ./.tox/py34/bin/activate
    (py34)$ cp ./examples/django/example/simple/config-template.py ./examples/django/example/simple/config.py
    (py34)$ vim ./examples/django/example/simple/config.py
    (py34)$ ./examples/django/example/manage.py runserver

Example of launching the :doc:`examples/flask-simple` with Python 2.6:

.. code-block:: bash

    $ . ./.tox/py26/bin/activate
    (py26)$ cp ./examples/flask/werkzeug_adapter/config-template.py ./examples/flask/werkzeug_adapter/config.py
    (py26)$ vim ./examples/flask/werkzeug_adapter/config.py
    (py26)$ python ./examples/flask/werkzeug_adapter/main.py

Example of launching the :doc:`examples/credentials` with Python 2.7:

.. note::

    The |gae| examples will only work in **Python 2.7**
    The |gae| command line tools are installed in the ``./tox/py27``
    virtual environment.

.. code-block:: bash

    $ . ./.tox/py27/bin/activate
    (py27)$ cp ./examples/gae/credentials/config-template.py ./examples/gae/credentials//config.py
    (py27)$ vim ./examples/gae/credentials/config.py
    (py27)$ dev_appserver ./examples/gae/credentials/
