# -*- coding: utf-8 -*-
from setuptools import find_packages
from setuptools import setup

setup(
    packages=find_packages(),
    package_data={'': ['*.txt', '*.rst']},
    extras_require={
        'OpenID': [
            "python-openid ; python_version<'3'",
            "python3-openid ; python_version>='3'",
        ],
        'test': [
            "jinja2",
            "liveandletdie",
            "pytest",
            "pyvirtualdisplay",
            "selenium",
        ]
    },
)
