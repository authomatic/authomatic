import os
import urllib
import zipfile
import platform
import subprocess


def after_install(options, home_dir):

    home_dir = os.path.abspath(home_dir)
    bootstrap_root = os.path.abspath(os.path.dirname(__file__))
    project_root = os.path.abspath(os.path.join(bootstrap_root, '..'))
    authomatic_path = os.path.join(project_root, 'authomatic')
    gae_examples_path = os.path.join(project_root, 'examples/gae')
    openid_path = os.path.join(home_dir, 'lib/python2.7/site-packages/openid')

    def _download_and_extract(url, extract_path):
        print('Downloading {}'.format(url))
        tmp_zip_path = urllib.urlretrieve(url)[0]
        zf = zipfile.ZipFile(tmp_zip_path)

        extract_path = os.path.join(home_dir, extract_path)
        extract_path = os.path.abspath(extract_path)
        print('Extracting {} to {}'.format(tmp_zip_path, extract_path))
        zf.extractall(os.path.join(home_dir, extract_path))

    def _add_pth(name, content):
        pth_path = 'lib/python2.7/site-packages/{}.pth'.format(name)
        with open(os.path.join(home_dir, pth_path), 'w') as pth:
            print('Creating PTH file: {}'.format(os.path.abspath(pth_path)))
            pth.writelines(content)

    def _link(target, name):
        try:
            print('creating symlink: {} -> {}'.format(name, target))
            os.symlink(target, name)
        except OSError:
            print('removing previous symlink: {}'.format(name))
            os.remove(name)
            print('creating symlink: {} -> {}'.format(name, target))
            os.symlink(target, name)

    architecture = platform.architecture()[0][:-3]

    _download_and_extract('https://chromedriver.googlecode.com/files/' +
                          'chromedriver_linux{}_2.2.zip'.format(architecture),
                          'bin')

    _download_and_extract('http://googleappengine.googlecode.com/files/' +
                          'google_appengine_1.8.3.zip',
                          'bin')

    _add_pth('authomatic', project_root)
    _add_pth('gae', '\n'.join([
            os.path.abspath(os.path.join(home_dir, 'bin/google_appengine/')),
            'import dev_appserver',
            'dev_appserver.fix_sys_path()',
        ]))

    for example in os.listdir(gae_examples_path):
        example_path = os.path.join(gae_examples_path, example)
        _link(authomatic_path, os.path.join(example_path, 'authomatic'))
        _link(openid_path, os.path.join(example_path, 'openid'))
