import logging

from authomatic.adapters import FlaskAdapter
from authomatic.providers import oauth2
from flask import Flask, jsonify
import authomatic

logger = logging.getLogger('authomatic.core')
logger.addHandler(logging.StreamHandler())

adapter = FlaskAdapter()
app = Flask(__name__)
app.config['SECRET_KEY'] = 'some random secret string'
authomatic.setup(
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


@app.route('/fb')
def index():
    result = authomatic.login(adapter, 'fb',
                              session=adapter.session,
                              session_saver=adapter.session_saver)
    if result:
        if result.error:
            return result.error.message
        elif result.user:
            if not (result.user.name and result.user.id):
                result.user.update()
            return jsonify(name=result.user.name, id=result.user.id)

    return ''


if __name__ == '__main__':
    app.run(debug=True)
