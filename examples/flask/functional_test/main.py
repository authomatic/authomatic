# encoding: utf-8
import logging

from flask import Flask, request
from flask.helpers import make_response
from flask.templating import render_template

import authomatic
from authomatic.adapters import WerkzeugAdapter
from tests.functional_tests import fixtures


DEBUG = True
SECRET_KEY = 'development key'
USERNAME = 'admin'
PASSWORD = 'default'

app = Flask(__name__)
app.config.from_object(__name__)

authomatic = authomatic.Authomatic(fixtures.ASSEMBLED_CONFIG, '123',
                                   report_errors=False,
                                   logger=app.logger)

@app.route('/')
def home():
    return fixtures.render_home()


@app.route('/login/<provider_name>', methods=['GET', 'POST'])
def login(provider_name):
    response = make_response()
    result = authomatic.login(WerkzeugAdapter(request, response),
                              provider_name)

    if result:
        response.data += fixtures.render_login_result(result).encode()

    return response


if __name__ == '__main__':
    # This does nothing unles you run this module with --testliveserver flag.
    import liveandletdie
    liveandletdie.Flask.wrap(app)
    
    app.run(debug=True, port=8080)
