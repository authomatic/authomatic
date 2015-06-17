"""Travis is blocking SMTP ports so this is for the time being useles."""

from email.mime.application import MIMEApplication
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.utils import formatdate
from glob import glob
import os
import smtplib

from tests.functional_tests import config


ME = os.path.dirname(__file__)
TESTS_DIR = os.path.join(ME, '..')


if __name__ == '__main__' and config.SEND_LOGS:
    print('connecting to {0}'.format(config.SMTP_HOST))
    smtpserver = smtplib.SMTP(config.SMTP_HOST, config.SMTP_PORT)
    smtpserver.ehlo()
    smtpserver.starttls()
    smtpserver.ehlo()
    print('Logging in')
    smtpserver.login(config.SMTP_LOGIN, config.SMTP_PASSWORD)

    repo = os.environ.get('TRAVIS_REPO_SLUG', '<repository>')
    branch = os.environ.get('TRAVIS_BRANCH', '<branch>')
    commit = os.environ.get('TRAVIS_COMMIT', '<commit>')
    pr = os.environ.get('TRAVIS_PULL_REQUEST', '<pull-request>')
    build = os.environ.get('TRAVIS_BUILD_NUMBER', '<build>')

    subject = ('Authomatic Travis CI logs of build #{0} ({1} | {2} | {3})'
               .format(build, repo, branch, commit))

    msg = MIMEMultipart(
        From=config.EMAIL_FROM,
        To=config.EMAIL_TO,
        Date=formatdate(localtime=True)
    )
    msg['Subject'] = subject
    msg.attach(MIMEText(
        "Authomatic Travis CI Logs\n\n"
        "Build:\t\t{build}\n"
        "Repository:\t{repo}\n"
        "Branch:\t\t{branch}\n"
        "Commit:\t\t{commit}\n"
        "Pull request:\t{pr}\n"
        .format(build=build, repo=repo, branch=branch, commit=commit, pr=pr)
    ))

    logs = glob(TESTS_DIR + '/functional_tests/*.log') + \
           glob(TESTS_DIR + '/*.log')

    print('Sending logs')

    for log in logs:
        filename = os.path.basename(log)
        print('  ' + filename)
        with open(log) as f:
            attachment = MIMEText(f.read())
            attachment.add_header('Content-Disposition', 'attachment',
                                  filename=filename)
            msg.attach(attachment)

    smtpserver.sendmail(config.SMTP_LOGIN, config.EMAIL_TO, msg.as_string())
    smtpserver.close()
    print('Done')