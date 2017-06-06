from setuptools import setup,find_packages

from authomatic import six


setup(
    name='Authomatic',
    version='0.1.0.post1', # TODO: Put version in one place.
    packages=find_packages(),
    package_data={'': ['*.txt', '*.rst']},
    author='Peter Hudec',
    author_email='peterhudec@peterhudec.com',
    description=('Authorization / authentication client library for '
                 'Python web applications'),
    long_description=open('README.rst').read(),
    keywords='authorization authentication oauth openid',
    url='http://peterhudec.github.io/authomatic',
    license = 'MIT',
    extras_require={
        'OpenID': ['python3-openid' if six.PY3 else 'python-openid'],
    },
    classifiers=[
        'Development Status :: 5 - Production/Stable',
        'Environment :: Web Environment',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
        'Programming Language :: JavaScript',
        'Topic :: Internet :: WWW/HTTP',
        'Topic :: Internet :: WWW/HTTP :: Dynamic Content :: '
            'CGI Tools/Libraries',
        'Topic :: Software Development :: Libraries :: Python Modules',
        'Topic :: System :: Systems Administration :: Authentication/Directory',
        'Topic :: Software Development :: Libraries',
        'Topic :: Software Development :: Libraries :: Python Modules',
    ]
)