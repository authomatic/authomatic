import os
import urllib
import zipfile
import platform
import sys


CHROMEDRIVER_VERSION = '2.8'
GAE_SDK_VERSION = '1.8.3'
CHROMEDRIVER_PATH_BASE = 'http://chromedriver.storage.googleapis.com/{}/'\
    .format(CHROMEDRIVER_VERSION)

ARCHITECTURE = platform.architecture()[0][:-3]
PLATFORM = platform.platform()


BOOTSTRAP_ROOT = os.path.abspath(os.path.dirname(__file__))
PROJECT_ROOT = os.path.abspath(os.path.join(BOOTSTRAP_ROOT, '..'))
AUTHOMATIC_PATH = os.path.join(PROJECT_ROOT, 'authomatic')
GAE_EXAMPLES_PATH = os.path.join(PROJECT_ROOT, 'examples/gae')

def after_install(options, home_dir):
    openid_path = os.path.join(home_dir, 'lib/python2.7/site-packages/openid')
    openid_path = os.path.abspath(openid_path)

    def _download_and_extract(url, extract_path):
        print('Downloading {0}'.format(url))
        tmp_zip_path = urllib.urlretrieve(url)[0]
        zf = zipfile.ZipFile(tmp_zip_path)

        extract_path = os.path.join(home_dir, extract_path)
        extract_path = os.path.abspath(extract_path)
        print('Extracting {0} to {1}'.format(tmp_zip_path, extract_path))
        zf.extractall(os.path.join(home_dir, extract_path))

    def _add_pth(name, content):
        python_version = '{0}.{1}'.format(*sys.version_info)
        pth_path = 'lib/python{0}/site-packages/{1}.pth'\
            .format(python_version, name)
        with open(os.path.join(home_dir, pth_path), 'w') as pth:
            print('Creating PTH file: {0}'.format(os.path.abspath(pth_path)))
            pth.writelines(content)

    def _link(target, name):
        try:
            print('creating symlink: {0} -> {1}'.format(name, target))
            os.symlink(target, name)
        except OSError:
            print('removing previous symlink: {0}'.format(name))
            os.remove(name)
            print('creating symlink: {0} -> {1}'.format(name, target))
            os.symlink(target, name)

    if PLATFORM.lower().startswith('darwin'):
        chromedriver_path = CHROMEDRIVER_PATH_BASE + 'chromedriver_mac32.zip'
    elif PLATFORM.lower().startswith('linux'):
        chromedriver_path = CHROMEDRIVER_PATH_BASE + \
            'chromedriver_linux{0}.zip'.format(ARCHITECTURE)
    elif PLATFORM.lower().startswith('win'):
        chromedriver_path = CHROMEDRIVER_PATH_BASE + 'chromedriver_win32.zip'
    else:
        chromedriver_path = None

    if chromedriver_path:
        _download_and_extract(chromedriver_path, 'bin')
        chromedriver_executable = os.path.join(home_dir, 'bin/chromedriver')
        print('Setting permissions of {0} to 755'
              .format(chromedriver_executable))
        os.chmod(chromedriver_executable, 755)

    _download_and_extract('http://googleappengine.googlecode.com/files/' +
                          'google_appengine_{0}.zip'.format(GAE_SDK_VERSION),
                          'bin')

    _add_pth('authomatic', PROJECT_ROOT)
    _add_pth('gae', '\n'.join([
            os.path.abspath(os.path.join(home_dir, 'bin/google_appengine/')),
            'import dev_appserver',
            'dev_appserver.fix_sys_path()',
        ]))

    for example in os.listdir(GAE_EXAMPLES_PATH):
        example_path = os.path.join(GAE_EXAMPLES_PATH, example)
        _link(AUTHOMATIC_PATH, os.path.join(example_path, 'authomatic'))
        _link(openid_path, os.path.join(example_path, 'openid'))