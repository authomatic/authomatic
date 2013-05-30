# -*- coding: utf-8 -*-
"""
Created by Mark Steve Samson http://marksteve.com
"""

import logging

from authomatic.extras.flask import FlaskAuthomatic
from authomatic.providers import oauth2
from flask import Flask, jsonify

logger = logging.getLogger('authomatic.core')
logger.addHandler(logging.StreamHandler())


app = Flask(__name__)
app.config['SECRET_KEY'] = 'some random secret string'

fa = FlaskAuthomatic(
    config={
        'fb': {
           'class_': oauth2.Facebook,
           'consumer_key': '###############',
           'consumer_secret': '################################',
           'scope': ['user_about_me', 'email', 'publish_stream'],
        },
    },
    secret=app.config['SECRET_KEY'],
    debug=True,
)


@app.route('/')
@fa.login('fb')
def index():
    if fa.result:
        if fa.result.error:
            return fa.result.error.message
        elif fa.result.user:
            if not (fa.result.user.name and fa.result.user.id):
                fa.result.user.update()
            return jsonify(name=fa.result.user.name, id=fa.result.user.id)
    else:
        return fa.response


if __name__ == '__main__':
    app.run(debug=True)
