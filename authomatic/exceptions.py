"""
Provides various exception types for the library.
"""


class BaseError(Exception):
    """
    Base error for all errors.
    """

    def __init__(self, message, original_message='', url='', status=None):
        super().__init__(message)

        #: Error message.
        self.message = message

        #: Original message.
        self.original_message = original_message

        #: URL related with the error.
        self.url = url

        #: HTTP status code related with the error.
        self.status = status

    def to_dict(self):
        return self.__dict__


class ConfigError(BaseError):
    pass


class SessionError(BaseError):
    pass


class CredentialsError(BaseError):
    pass


class HTTPError(BaseError):
    pass


class CSRFError(BaseError):
    pass


class ImportStringError(BaseError):
    pass


class AuthenticationError(BaseError):
    pass


class OAuth1Error(BaseError):
    pass


class OAuth2Error(BaseError):
    pass


class OpenIDError(BaseError):
    pass


class CancellationError(BaseError):
    pass


class FailureError(BaseError):
    pass


class FetchError(BaseError):
    pass


class RequestElementsError(BaseError):
    pass
