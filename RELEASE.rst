Releasing
=========

Release are triggered by creating a tag ``trigger-x.y.z`` and pushing it to the ``master`` branch on GitHub (`TravisCI <https://travis-ci.org/authomatic/authomatic/>`_).
The release process removes this tag and replaces it with a version tag ``x.y.z``. (`zest.releaser <https://zestreleaser.readthedocs.io/>`_).
While release the ``news/*`` files are turned automatically into a nicely formatted ``CHANGES.rst`` (`towncrier <https://towncrier.readthedocs.io/>`_).
The documentation will be built and pushed to GH-pages (`Sphinx <http://www.sphinx-doc.org/>`_).

The steps for generating an automated release are:

- Edit ``setup.cfg`` and check or modify the the version number as required:
    - The micro version will have been automatically incremented by the last release, and ``.dev0`` appended.
    - Keep the ``.dev0`` postfix, the release process will take care of it.
    - Check ``news/`` directory for feature and/or breaking changes and increase minor or major version number if needed (and not already done).
        - There must be at least one committed entry in ``news/`` for a release to succeed.
        - If updating the version, follow `PEP440 <https://www.python.org/dev/peps/pep-0440/>`_ and `Semantic Versioning 2 <https://semver.org/>`_
- ``git tag trigger-x.y.z`` the release (with ``x.y.z`` the release number).
    - Technically the tag name postfix is irrelevant for the release, but we mirror the version number to make our intention clear.
- Push the code and tags to the ``master`` branch
    -  ``git push``
    - ``git push --tags``
- Once Travis completes, check the deployments were successful
    - `PyPI <https://pypi.org/project/Authomatic/#history>`_ (as ``bdist_wheel`` and ``sdist`` (egg)).
    - `Authomatic documentation <https://authomatic.github.io/authomatic/>`_
