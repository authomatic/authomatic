"""
Interfaces
^^^^^^^^^^

If you want to implement framework specific extras, use these abstract
classes as bases:

"""

import abc


class BaseSession:
    """
    Abstract class for custom session implementations.
    """

    __metaclass__ = abc.ABCMeta

    @abc.abstractmethod
    def save(self):
        """
        Called only once per request.

        Should implement a mechanism for setting the the session
        **cookie** and saving the session **data** to storage.

        """

    @abc.abstractmethod
    def __setitem__(self, key, value):
        """
        Same as :meth:`dict.__setitem__`.
        """

    @abc.abstractmethod
    def __getitem__(self, key):
        """
        Same as :meth:`dict.__getitem__`.
        """

    @abc.abstractmethod
    def __delitem__(self, key):
        """
        Same as :meth:`dict.__delitem__`.
        """

    @abc.abstractmethod
    def get(self, key):
        """
        Same as :meth:`dict.get`.
        """


class BaseConfig:
    """
    Abstract class for :doc:`config` implementations.
    """

    __metaclass__ = abc.ABCMeta

    @abc.abstractmethod
    def get(self, key):
        """
        Same as :attr:`dict.get`.
        """

    @abc.abstractmethod
    def values(self):
        """
        Same as :meth:`dict.values`.
        """
