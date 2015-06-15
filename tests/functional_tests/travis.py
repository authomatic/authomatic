import os

import liveandletdie

ME = os.path.dirname(__file__)
HOST = '127.0.0.1'
PORT = 8080


app = liveandletdie.Flask(
    os.path.join(ME, '../../examples/flask/functional_test/main.py'),
    host=HOST,
    port=PORT,
    check_url='https://authomatic.com:8080',
    logging=True,
    ssl=True,
)

print('check url = {0}'.format(app.check_url))
app.live(kill_port=True)
print('lives')

app.die()