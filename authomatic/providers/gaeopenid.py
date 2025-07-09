"""
Google App Engine OpenID Providers
----------------------------------

|openid|_ provider implementations based on the |gae_users_api|_.

.. note::

    When using the :class:`GAEOpenID` provider, the :class:`.User` object
    will always have only the
    :attr:`.User.user_id`,
    :attr:`.User.email`,
    :attr:`.User.gae_user`
    attributes populated with data.
    Moreover the :attr:`.User.user_id` will always be empty on the
    `GAE Development Server
    <https://developers.google.com/appengine/docs/python/tools/devserver>`_.

.. autosummary::

    GAEOpenID
    Yahoo
    Google

"""

import authomatic.core as core
from authomatic import providers
from authomatic.exceptions import FailureError

import logging

logger = logging.getLogger(__name__)

try:
    from google.appengine.api import users
except ImportError:
    logger.exception("FATAL: google.appengine 1st Gen. not installed!")
    users = None


__all__ = ["GAEOpenID", "Yahoo", "Google"]


class GAEOpenID(providers.AuthenticationProvider):
    """
    |openid|_ provider based on the |gae_users_api|_.

    Accepts additional keyword arguments inherited from
    :class:`.AuthenticationProvider`.

    """

    @providers.login_decorator
    def login(self):
        """
        Launches the OpenID authentication procedure.
        """

        if self.params.get(self.identifier_param):
            # =================================================================
            # Phase 1 before redirect.
            # =================================================================
            self._log(logging.INFO, "Starting OpenID authentication procedure.")

            url = users.create_login_url(
                dest_url=self.url, federated_identity=self.identifier
            )

            self._log(logging.INFO, f"Redirecting user to {url}.")

            self.redirect(url)
        else:
            # =================================================================
            # Phase 2 after redirect.
            # =================================================================

            self._log(
                logging.INFO,
                "Continuing OpenID authentication procedure after redirect.",
            )

            user = users.get_current_user()

            if user:
                self._log(logging.INFO, "Authentication successful.")
                self._log(logging.INFO, "Creating user.")
                self.user = core.User(
                    self,
                    id=user.federated_identity(),
                    email=user.email(),
                    gae_user=user,
                )

                # =============================================================
                # We're done
                # =============================================================
            else:
                raise FailureError(
                    f'Unable to authenticate identifier "{self.identifier}"!'
                )


class Yahoo(GAEOpenID):
    """
    :class:`.GAEOpenID` provider with the :attr:`.identifier` set to
    ``"me.yahoo.com"``.
    """

    identifier = "me.yahoo.com"


class Google(GAEOpenID):
    """
    :class:`.GAEOpenID` provider with the :attr:`.identifier` set to
    ``"https://www.google.com/accounts/o8/id"``.
    """

    identifier = "https://www.google.com/accounts/o8/id"
