from setuptools import setup,find_packages

setup(
    name='Authomatic',
    version='0.0.5',
    packages=find_packages(),
    package_data={'': ['*.txt', '*.rst']},
    author='Peter Hudec',
    author_email='peterhudec@peterhudec.com',
    description='Authorization / authentication client library for Python web applications',
    long_description=open('README.rst').read(),
    keywords='authorization authentication oauth openid',
    url='http://peterhudec.github.io/authomatic',
    license = 'MIT',
    extras_require={
        'OpenID': ['python-openid'],
    },
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Environment :: Web Environment',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: JavaScript',
        'Topic :: Internet :: WWW/HTTP',
        'Topic :: Internet :: WWW/HTTP :: Dynamic Content :: CGI Tools/Libraries',
        'Topic :: Software Development :: Libraries :: Python Modules',
        'Topic :: System :: Systems Administration :: Authentication/Directory',
        'Topic :: Software Development :: Libraries',
        'Topic :: Software Development :: Libraries :: Python Modules',
    ]
)