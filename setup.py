from setuptools import find_packages
from setuptools import setup

oid_reqs = [
    "python-openid ; python_version<'3'",
    "python3-openid ; python_version>='3'",
]

setup(
    packages=find_packages(),
    package_data={"": ["*.txt", "*.rst"]},
    extras_require={
        'OpenID: python_version < "3"': ["python-openid"],
        'OpenID: python_version >= "3"': ["python3-openid"],
    },
)
