Releasing
=========

Release are triggered by creating a tag ``trigger-x.y.z`` and pushing it to GitHub.
The release process removes the tag and replaces it with a version tag ``x.y.z``.
While release the ``news/*`` files are turned automatically into a nicely formatted ``CHANGES.rst``.
If on ``master`` branch the documentation on GH-pages will be updated too.

The steps for generating an automated release are:

- Edit ``setup.cfg`` and check the the version number. Minor was already increased after last release and a ``dev0`` was appended.
    - follow `PEP440 <https://www.python.org/dev/peps/pep-0440/>`_ and
    - follow `Semantic Versioning 2 <https://semver.org/>`_
    - check ``/news`` directory for feature and/or breaking changes and increase minor or major version number if needed (and not already done) in ``setup.cfg``.
    - keep the ``.dev0`` postfix, the release process will take care of it.
- ``git tag trigger-x.y.z`` the release (with ``x.y.z`` the release number).
    - technical the tag name is irrelevant for the release, but we agree to mirror the version number and prefix with ``trigger-``.
    - Push to master branch; other branches will do the pre/post-release but not actually upload anything to PyPI.
    - Make sure to do ``git push --tags``
- Travis will then release to `PyPI <https://pypi.org/project/Authomatic/#history>`_ as ``bdist_wheel`` and ``sdist`` (egg).
- After deployment the `Authomatic documentation <https://authomatic.github.io/authomatic/>`_ will get build and updated on GitHub Pages
  (only tags on master branch).
