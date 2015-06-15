import os

import liveandletdie

ME = os.path.dirname(__file__)
HOST = '127.0.0.1'
PORT = 8080


app = liveandletdie.Flask(
    os.path.join(ME, '../../examples/flask/functional_test/main.py'),
    host=HOST,
    port=PORT,
    check_url='authomatic.com',
    logging=True,
    ssl=True,
)

app.live()
print('x' * 100)
app.die()