# encoding: utf-8
import abc

from selenium.webdriver.common.keys import Keys


class BaseProviderFixture(object):
    """
    Base class for provider fixtures.

    Provides mechanisms of logging the user in by a provider and consenting
    to grant access to the tested application.
    """

    __metaclass__ = abc.ABCMeta

    def __init__(self, login, password):
        """

        :param str login:
            User login

        :param str password:
            User password

        """

        self.login = login
        self.password = password

    PRE_LOGIN_CLICKS_XPATH = []

    @abc.abstractproperty
    def LOGIN_XPATH(self):
        pass

    @abc.abstractproperty
    def PASSWORD_XPATH(self):
        pass

    @abc.abstractproperty
    def CONSENT_XPATHS(self):
        pass

    @property
    def login_function(self):
        """
        Fills out and submits provider a login form.

        :param str login_xpath:
            The XPath of the input element where the user should enter his username.

        :param str password_xpath:
            The XPath of the input element where the user should enter his password.

        :param str login:
            The user's username.

        :param str password:
            The user's password.
        """

        def f(browser):
            for xpath in self.PRE_LOGIN_CLICKS_XPATH:
                print('clicking on {0}'.format(xpath))
                browser.find_element_by_xpath(xpath).click()

            print('logging the user in.')
            browser.find_element_by_xpath(self.LOGIN_XPATH)\
                .send_keys(self.login)
            password_element = browser.\
                find_element_by_xpath(self.PASSWORD_XPATH)
            print 'PASSWORD = {0}'.format(self.password)
            password_element.send_keys(self.password)
            password_element.send_keys(Keys.ENTER)
        return f

    @property
    def consent_function(self):
        """
        Clicks a consent button specified by the XPath if it exists recursively.

        :param str xpath:
            The XPath of the consent button.
        """

        def f(browser):
            for path in self.CONSENT_XPATHS:
                try:
                    button = browser.find_element_by_xpath(path)
                    print('Hitting consent button.')
                    button.click()
                    f(browser)
                except Exception as e:
                    print('No consent needed.')
                    pass
        return f


class BitlyFixture(BaseProviderFixture):
    PRE_LOGIN_CLICKS_XPATH = ['//*[@id="oauth_access"]/form/div/div[1]/a']
    LOGIN_XPATH = '//*[@id="username"]'
    PASSWORD_XPATH = '//*[@id="password"]'
    CONSENT_XPATHS = ['//*[@id="oauth_access"]/form/button[1]']


class DeviantART(BaseProviderFixture):
    LOGIN_XPATH = '//*[@id="username"]'
    PASSWORD_XPATH = '//*[@id="password"]'
    CONSENT_XPATHS = [
        '//*[@id="terms_agree"]',
        '//*[@id="authorize_form"]/fieldset/div[2]/div[2]/a[1]',
    ]


class FacebookFixture(BaseProviderFixture):
    LOGIN_XPATH = '//*[@id="email"]'
    PASSWORD_XPATH = '//*[@id="pass"]'
    CONSENT_XPATHS = [
        '//*[@id="platformDialogForm"]/div[2]/div/table/tbody/tr/td[2]/'
        'button[1]',
    ]


class FoursquareFixture(BaseProviderFixture):
    LOGIN_XPATH = '//*[@id="username"]'
    PASSWORD_XPATH = '//*[@id="password"]'
    CONSENT_XPATHS = [
        '//*[@id="loginFormButton"]',
    ]


class GoogleFixture(BaseProviderFixture):
    LOGIN_XPATH = '//*[@id="Email"]'
    PASSWORD_XPATH = '//*[@id="Passwd"]'
    CONSENT_XPATHS = [
        '//*[@id="submit_approve_access"]',
    ]


class GitHubFixture(BaseProviderFixture):
    LOGIN_XPATH = '//*[@id="login_field"]'
    PASSWORD_XPATH = '//*[@id="password"]'
    CONSENT_XPATHS = [
        '//*[@id="login"]/form/div[3]/input[4]',
        '//*[@id="site-container"]/div/div[2]/form/p/button',
    ]
