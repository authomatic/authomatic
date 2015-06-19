import os
import subprocess

from tests.functional_tests import config


if __name__ == '__main__':
    os.environ['GIT_LOGS'] = config.GIT_LOGS
    os.environ['GIT_REPO'] = config.GIT_REPO
    os.environ['GIT_BRANCH'] = config.GIT_BRANCH
    os.environ['GIT_USER'] = config.GIT_USER
    os.environ['GIT_PASSWORD'] = config.GIT_PASSWORD

    subprocess.call(["sh", "tests/travis/git-logs.sh"])
