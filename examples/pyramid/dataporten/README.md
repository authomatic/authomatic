Simple login example for Dataporten using Pyramid and Authomatic
================================================================

To run it on your local machine:
- Download main.py
- Install pyramid and Authomatic, e.g. to your virtualenv:
```
    pip install pyramid
    pip install git+https://github.com/authomatic/authomatic.git
```
- Visit https://dashboard.dataporten.no and register a new
  application. Name it whatever you like and use
  `http://localhost:8080/login` as 'Redirect URL'.
- Visit 'Scopes' on the dashboard, and choose 'profile', 'openid' and
  'email'.
- Visit 'OAuth details' on the dashboard and find 'Client ID' and
  'Client Secret'.
- Edit CONFIG['dp'] in main.py, setting 'consumer_key' to 'Client ID'
  from the dashboard and 'consumer_secret' to 'Client Secret'
- Run main.py
```
    python main.py
```
- Visit http://localhost:8080 and press the login link.
- When logged in, the page will show your name, ID and email.
- If port 8080 is already in use, edit main.py to choose another port.

The example has been tested with python 2.7.14 and python 3.6.4.
