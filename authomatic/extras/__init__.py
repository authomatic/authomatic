"""
Implement Adapters
------------------

Implementing an adapter for a Python web framework is easy.

You do it by subclassing the :class:`.BaseAdapter` abstract class.
There are only **nine** members that you need to implement and
the only complicated one is the :attr:`.BaseAdapter.openid_store`.

Moreover if your framework is based on the |webob|_ library
you can use the :class:`.WebObBaseAdapter` and you only need to
implement **three** members.

.. autoclass:: BaseSession
    :members: __setitem__, __getitem__, __delitem__, get
    :special-members:

"""

from _pyio import __metaclass__
from urllib import urlencode
import abc
import authomatic
import binascii
import hashlib
import hmac
import logging
import random
import time
import urllib


class BaseSession(object):
    """
    Interface for :attr:`.BaseAdapter.session`.
    """
    
    __metaclass__ = abc.ABCMeta
    
    @abc.abstractmethod
    def __setitem__(self, key, value):
        """
        Same as :attr:`dict.__setitem__`.
        
        :param key:
        :param value:
        """
    
    
    @abc.abstractmethod
    def __getitem__(self, key):
        """
        Same as :attr:`dict.__getitem__`.
        
        :param key:
        """
    
    
    @abc.abstractmethod
    def __delitem__(self, key):
        """
        Same as :attr:`dict.__delitem__`.
        
        :param key:
        """
    
    
    @abc.abstractmethod
    def get(self, key):
        """
        Same as :attr:`dict.get`.
        
        :param key:
        """


class BaseConfig(object):
    
    __metaclass__ = abc.ABCMeta
    
    @abc.abstractmethod
    def get(self, key):
        """
        
        :param key:
        """
    
    @abc.abstractmethod
    def values(self):
        """
        
        """        









