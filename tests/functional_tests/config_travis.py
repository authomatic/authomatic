# -*- coding: utf-8 -*-
import datetime
import codecs
import os
import pickle
import sys

from pyvirtualdisplay import Display
from selenium import webdriver

import config
import constants


# Choose and configure the browser of your choice
def get_browser():
    global display
    display = Display(visible=0, size=(1024, 768))
    display.start()
    return webdriver.Firefox()


def teardown():
    global display
    display.stop()


MAX_LOGIN_ATTEMPTS = 10

# The host and port where the tested ap shoud listen.
HOST = '127.0.0.1'
PORT = 8080

# The host alias set in the /etc/hosts file.
# The actual tests will navigate selenium browser to this host.
# This is necessary because some providers don't support localhost as the
# callback url.
HOST_ALIAS = 'authomatic.com'

# Only frameworks included here will be tested.
INCLUDE_FRAMEWORKS = [
    # 'django',
    'flask', # Runs with https
    # 'pyramid',
]

INCLUDE_PROVIDERS = [
    # OAuth 1.0a
    # 'bitbucket',
    # 'flickr',
    # 'plurk',
    'twitter',
    # 'tumblr',
    # # 'ubuntuone',  # UbuntuOne service is no longer available
    # 'vimeo',
    # 'xero',
    # 'xing',
    # 'yahoo',
    #
    # # OAuth 2.0
    # 'amazon',
    # # 'behance',  # doesn't support third party authorization anymore.
    # 'bitly',
    # 'deviantart',
    'facebook',
    # 'foursquare',
    # 'google',
    # 'github',
    # 'linkedin',
    # 'paypal',
    # 'reddit',
    # 'vk',
    # 'windowslive',
    # 'yammer',
    # 'yandex',
    #
    # # OpenID
    # 'openid_livejournal',
    'openid_verisignlabs',
    # 'openid_wordpress',
    # 'openid_yahoo',
]

if __name__ == '__main__':
    travis_config = {}
    travis_config['common'] = config.COMMON
    travis_config['providers'] = config.PROVIDERS
    pickled = codecs.encode(pickle.dumps(travis_config, 2), "base64").decode()
    sys.stdout.write(pickled)
else:
    pickled = os.environ.get('FUNCTIONAL_TESTS_CONFIG')
    if pickled:
        unpickled = pickle.loads(codecs.decode(pickled.encode(), "base64"))
    else:
        raise Exception('The "FUNCTIONAL_TESTS_CONFIG" environmental variable '
                        'must be set in the Travis CI environment.')

    COMMON = unpickled['common']
    PROVIDERS = unpickled['providers']

