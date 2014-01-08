import os

import virtualenv


if __name__ == '__main__':
    base_path = os.path.abspath(os.path.dirname(__file__))
    with open(os.path.join(base_path, 'bootstrapsrc.py')) as src:
        with open(os.path.join(base_path, 'bootstrap.py'), 'w') as output:
            output.write(virtualenv.create_bootstrap_script(src.read()))