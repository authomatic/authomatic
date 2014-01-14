# encoding: utf-8
import abc

from selenium.webdriver.common.keys import Keys


class BaseProviderFixture(object):

    __metaclass__ = abc.ABCMeta

    def __init__(self, login, password):
        self.login = login
        self.password = password

    @abc.abstractproperty
    def LOGIN_XPATH(self):
        pass

    @abc.abstractproperty
    def PASSWORD_XPATH(self):
        pass

    @abc.abstractproperty
    def CONSENT_XPATH(self):
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
            print('logging the user in.')
            browser.find_element_by_xpath(self.LOGIN_XPATH)\
                .send_keys(self.login)
            password_element = browser.\
                find_element_by_xpath(self.PASSWORD_XPATH)
            print 'PASSWORD = {}'.format(self.password)
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
            try:
                button = browser.find_element_by_xpath(self.CONSENT_XPATH)
                print('Hitting consent button.')
                button.click()
                f(browser)
            except Exception as e:
                print('No consent needed.')
                pass
        return f


class FacebookFixture(BaseProviderFixture):
    LOGIN_XPATH = '//*[@id="email"]'
    PASSWORD_XPATH = '//*[@id="pass"]'
    CONSENT_XPATH = '//*[@id="platformDialogForm"]/div[2]' \
                    '/div/table/tbody/tr/td[2]/button[1]'
