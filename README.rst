
Authomatic
==========

Forked from **Authomatic** which
is a **framework agnostic** library
for **Python** web applications
with a **minimalistic** but **powerful** interface
which simplifies **authentication** of users
by third party providers like **Facebook** or **Twitter**
through standards like **OAuth** and **OpenID**.

For more info visit the project page at http://peterhudec.github.io/authomatic.

Features
========

* Added new client credentials grant type authorization for users

Usage
=====

Read the exhaustive documentation at http://peterhudec.github.io/authomatic.
Just a small change in configuring your providers, just mention the grant type
for your authorization flow in the provider class like this

for Client credential grant type
    ```
    grant_type = AuthorizationProvider.CLIENT_CREDENTIALS_GRANT_TYPE
    ```

for authorization code grant type
    ```
    grant_type = AuthorizationProvider.AUTHORIZATION_CODE_GRANT_TYPE
    ```

The default grant_type is also AUTHORIZATION_CODE_GRANT_TYPE so if you
don't mention the grant type it will automatically assume it to be 
AUTHORIZATION_CODE_GRANT_TYPE.
