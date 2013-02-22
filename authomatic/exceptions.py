class BaseError(Exception):
    def __init__(self, message, original_message='', url='', code=None):
        super(BaseError, self).__init__(message)        
        self.message = message
        self.original_message = original_message
        self.url = url
        self.code = code


class ConfigError(BaseError):
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


