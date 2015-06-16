import os
from urllib2 import urlopen

import liveandletdie
import OpenSSL

ME = os.path.dirname(__file__)
HOST = '127.0.0.1'
PORT = 8080


app = liveandletdie.Flask(
    os.path.join(ME, '../../examples/flask/functional_test/main.py'),
    host=HOST,
    port=PORT,
    check_url='http://authomatic.com:8080',
    # ssl=True,
    logging=True
)

print('check url = {0}'.format(app.check_url))
app.live(kill_port=True)
print('lives')

app.die()