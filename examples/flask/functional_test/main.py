# encoding: utf-8
from flask import Flask, request
from flask.helpers import make_response
from flask.templating import render_template

import authomatic
from authomatic.adapters import WerkzeugAdapter
from tests.functional_tests import config


DEBUG = True
SECRET_KEY = 'development key'
USERNAME = 'admin'
PASSWORD = 'default'

app = Flask(__name__)
app.config.from_object(__name__)

authomatic = authomatic.Authomatic(config.PROVIDERS, '123')

@app.route('/')
def home():
    return render_template('index.html', providers=config.PROVIDERS.keys())


@app.route('/login/<provider_name>/', methods=['GET', 'POST'])
def login(provider_name):
    response = make_response()
    result = authomatic.login(WerkzeugAdapter(request, response), provider_name)
    if result:
        if result.user:
            result.user.update()
        user_properties = config.PROVIDERS.values()[0]['user'].keys()
        return render_template('login.html', result=result,
                               providers=config.PROVIDERS.keys(),
                               user_properties=user_properties)
    
    # Don't forget to return the response.
    return response


if __name__ == '__main__':
    
    # This does nothing unles you run this module with --testliveserver flag.
    import liveandletdie
    liveandletdie.Flask.wrap(app)
    
    app.run(debug=True, port=8080)