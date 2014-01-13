# encoding: utf-8
import abc

from selenium.webdriver.common.keys import Keys


class ProviderFixture(object):

    __metaclass__ = abc.ABCMeta

    def __init__(self, login_xpath, password_xpath, consent_xpath):
        self.login_xpath = login_xpath
        self.password_xpath = password_xpath
        self.consent_xpath = consent_xpath

    def login(self, login, password):
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
            browser.find_element_by_xpath(self.login_xpath)\
                .send_keys(login)
            password_element = browser.\
                find_element_by_xpath(self.password_xpath)
            password_element.send_keys(password)
            password_element.send_keys(Keys.ENTER)
        return f

    @property
    def consent(self):
        """
        Clicks a consent button specified by the XPath if it exists recursively.

        :param str xpath:
            The XPath of the consent button.
        """

        def f(browser):
            try:
                button = browser.find_element_by_xpath(self.consent_xpath)
                print('Hitting consent button.')
                button.click()
                f(browser)
            except Exception as e:
                print('No consent needed.')
                pass
        return f


FACEBOOK = ProviderFixture(login_xpath='//*[@id="email"]',
                           password_xpath='//*[@id="pass"]',
                           consent_xpath='//*[@id="platformDialogForm"]/div[2]'
                           '/div/table/tbody/tr/td[2]/button[1]')
