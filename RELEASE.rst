Releasing
=========

The steps for generating an automated release are:

- Edit ``setup.cfg`` and ``CHANGES.rst`` and bump the version number.
    - follow `PEP440 <https://www.python.org/dev/peps/pep-0440/>`_ and
    - `Semantic Versioning 2 <https://semver.org/>`_
- ``git tag x.y.z`` the release (with `x.y.z` the release number).
    - technical the tag name is irrelevant for the release, but we agree to mirror the version number.
- Push to master branch
    - all other branches are ignored, tagged or otherwise.
    - Make sure to do ``git push --tags``
- Travis will then release to `PyPI <https://pypi.org/project/Authomatic/#history>`_ as ``bdist_wheel`` and ``sdist`` (egg).
- After deployment the `Authomatic documentation <https://authomatic.github.io/authomatic/>`_ will get build and updated on GitHub Pages
  (only tags on master branch).
