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
    return fixtures.render_home('flask')


@app.route('/login/<provider_name>', methods=['GET', 'POST'])
def login(provider_name):
    response = make_response()
    result = authomatic.login(WerkzeugAdapter(request, response),
                              provider_name)

    if result:
        response.data += fixtures.render_login_result('flask', result).encode()

    return response


if __name__ == '__main__':

    # if not app.debug:
    import logging

    file_handler = logging.FileHandler('flask.log')
    # file_handler.setLevel(logging.WARNING)
    app.logger.addHandler(file_handler)

    # This does nothing unless you run this module with --testliveserver flag.
    import liveandletdie
    liveandletdie.Flask.wrap(app)

    app.run(debug=True, port=8080)
