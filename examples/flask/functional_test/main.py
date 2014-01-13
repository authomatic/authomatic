# encoding: utf-8
from flask import Flask, request
from flask.helpers import make_response
from flask.templating import render_template

import authomatic
from authomatic.adapters import WerkzeugAdapter
from tests.functional_tests.config import CONFIG


DEBUG = True
SECRET_KEY = 'development key'
USERNAME = 'admin'
PASSWORD = 'default'

app = Flask(__name__)
app.config.from_object(__name__)

authomatic = authomatic.Authomatic(CONFIG, '123')

@app.route('/')
def home():
    return render_template('index.html', config=CONFIG)

@app.route('/login/<provider_name>/', methods=['GET', 'POST'])
def login(provider_name):
    response = make_response()
    result = authomatic.login(WerkzeugAdapter(request, response), provider_name)
    if result:
        if result.user:
            result.user.update()
        return render_template('login.html', result=result)
    
    # Don't forget to return the response.
    return response


if __name__ == '__main__':
    
    # This does nothing unles you run this module with --testliveserver flag.
    import liveandletdie
    liveandletdie.Flask.wrap(app)
    
    app.run(debug=True, port=8080)