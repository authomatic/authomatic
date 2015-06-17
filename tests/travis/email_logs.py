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


if __name__ == '__main__':
    smtpserver = smtplib.SMTP("smtp.gmail.com",587)
    smtpserver.ehlo()
    smtpserver.starttls()
    smtpserver.ehlo()
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
        "Authomatic Travis CI logs\n"
        "-------------------------\n\n"
        "Build:\t\t{build}\n"
        "Repository:\t{repo}\n"
        "Branch:\t\t{branch}\n"
        "Commit:\t\t{commit}\n"
        "Pull request:\t{pr}\n"
        .format(build=build, repo=repo, branch=branch, commit=commit, pr=pr)
    ))

    logs = glob(TESTS_DIR + '/functional_tests/*.log') + glob(ME + '/*.log')

    for log in logs:
        with open(log) as f:
            attachment = MIMEText(f.read())
            attachment.add_header('Content-Disposition', 'attachment', filename=os.path.basename(log))
            msg.attach(attachment)

    print('Sending logs to {0}'.format(config.EMAIL_TO))
    smtpserver.sendmail(config.SMTP_LOGIN, config.EMAIL_TO, msg.as_string())
    smtpserver.close()