import datetime
import logging
import simpleauth2
import urlparse

HTTP_METHODS = ('GET', 'HEAD', 'POST', 'PUT', 'DELETE', 'TRACE', 'OPTIONS', 'CONNECT', 'PATCH')

QUERY_STRING_PARSER = 'query_string_parser'
JSON_PARSER = 'json_parser'


def _login_decorator(func):
    """
    
    """
    
    def wrap(provider, *args, **kwargs):
        error = None
        try:
            func(provider, *args, **kwargs)
        except Exception as e:
            if provider.report_errors:
                error = e
                provider._log(logging.ERROR, 'Reported supressed exception: {}!'.format(repr(error)))
            else:
                raise
        finally:
            event = simpleauth2.LoginResult(provider, error)
            if provider.user or error:
                if provider.callback:
                    provider.callback(event)
                    provider._log(logging.INFO, 'Procedure finished.')
                return event
    return wrap


class BaseProvider(object):
    """
    Base class for all providers
    """
    
    def __init__(self, adapter, provider_name, consumer, callback=None,
                 short_name=None, report_errors=True, logging_level=logging.INFO):
        self.provider_name = provider_name
        self.consumer = consumer
        self.callback = callback
        self.adapter = adapter
        self.short_name = short_name
        self.report_errors = report_errors
        
        self.user = None
                
        self._user_info_request = None
        
        # setup logger
        self.logger = logging.getLogger(__name__)
        self.logger.setLevel(logging_level)
        if logging_level in (None, False):
            self.logger.disabled = False
        
        # recreate full current URL
        self.uri = self.adapter.get_current_uri()
    
    
    #=======================================================================
    # Static properties to be overriden by subclasses
    #=======================================================================
    
    
    # tuple of callables which parse responses returned by providers ordered by their usage
    parsers = (lambda content: content, )
    
    # Override this property to fix different naming conventions for user info values returned by providers.
    # keys are the names of the User class properties
    # values are either strings specifiing which key of the data dictionary should be used,
    # or callables expecting the data dictionary as argument and returning the desired value
    user_info_mapping = {}
    
    has_protected_resources = False
    
    #===========================================================================
    # Methods to be overriden by subclasses
    #===========================================================================
    
    @_login_decorator
    def login(self, *args, **kwargs):
        raise NotImplementedError
    
    
    #===========================================================================
    # Exposed methods
    #===========================================================================
    
    @classmethod
    def get_type(cls):
        return cls.__module__ + '.' + cls.__bases__[0].__name__
    
    @staticmethod
    def create_url(url_type, base):
        raise NotImplementedError
    
    #TODO: useless?
    def update_user(self):
        return self.user
    
    
    #===========================================================================
    # Internal methods
    #===========================================================================
    
    @classmethod
    def _create_request_elements(cls, request_type, url, method='GET'):
        raise NotImplementedError
    
    
    def _log(self, level, msg):
        base = 'SimpleAuth:{}: '.format(self.__class__.__name__)
        self.logger.log(level, base + msg)
        
    
    def _fetch(self, *args, **kwargs):
        return self.adapter.fetch_async(*args, **kwargs).get_response()
        
    
    def _update_or_create_user(self, data, credentials=None):
        """
        Updates the properties of the self.user object.
        
        Takes into account the self.user_info_mapping property.
        """
        
        if not self.user:
            self._log(logging.INFO, 'Creating user.')
            self.user = simpleauth2.User(self, credentials=credentials)
        else:
            self._log(logging.INFO, 'Updating user.')
        
        self.user.raw_user_info = data
        
        # iterate over User properties
        for key in self.user.__dict__.keys():
            # exclude raw_user_info
            if key is not 'raw_user_info':
                
                # check if there is a diferent key in the user_info_mapping
                data_key = self.user_info_mapping.get(key) or key
                
                if type(data_key) is str:
                    # get value from data
                    new_value = data.get(data_key)
                elif callable(data_key):
                    new_value = data_key(data)
                else:
                    raise Exception('The values of the user_info_mapping dict must be a string or callable. {} found under "{}" key.'.format(type(data_key), key))                
                
                # update user
                if new_value:
                    setattr(self.user, key, new_value)
        
        return self.user
    
    
    def _normalize_scope(self, scope):
        """
        Convert scope list to csv
        """
        
        return ','.join(scope) if scope else None
        
    
    def _get_parser_by_index(self, index):
        return getattr(self.adapter, self.parsers[index])
    
    
    def _check_consumer(self):
        if not self.consumer.key:
            raise simpleauth2.exceptions.ConfigError('Consumer key not specified for provider {}!'.format(self.provider_name))
        
        if not self.consumer.secret:
            raise simpleauth2.exceptions.ConfigError('Consumer secret not specified for provider {}!'.format(self.provider_name))


class AuthorisationProvider(BaseProvider):
    
    has_protected_resources = True
    
    USER_AUTHORISATION_REQUEST_TYPE = 2
    ACCESS_TOKEN_REQUEST_TYPE = 3
    PROTECTED_RESOURCE_REQUEST_TYPE = 4
    
    user_authorisation_url = ''
    access_token_url = ''
    user_info_url = ''
    
    @staticmethod
    def _split_url(url):
        "Splits given url to url base and params converted to list of tuples"
        
        split = urlparse.urlsplit(url)
        
        base = urlparse.urlunsplit((split.scheme, split.netloc, split.path, 0, 0))
        
        params = urlparse.parse_qsl(split.query, True)
        
        return base, params
    
    
    @staticmethod
    def to_tuple(credentials):
        raise NotImplementedError
    
    
    @staticmethod
    def reconstruct(tuple_):
        raise NotImplementedError
    
    
    def create_request(self, url, method='GET', content_parser=None, response_parser=None):       
        return simpleauth2.Request(adapter=self.adapter,
                       url=url,
                       credentials=self.user.credentials,
                       method=method,
                       content_parser=content_parser,
                       response_parser=response_parser)
        
    
    def fetch_user_info(self):
        return self.user_info_request.fetch().get_response()
    
    
    @property
    def user_info_request(self):
        if not self._user_info_request:
            
            def response_parser(response, content_parser):
                response = self.adapter.response_parser(response, content_parser)
                self.user = self._update_or_create_user(response.data)
                return simpleauth2.UserInfoResponse(response, self.user)
            
            self._user_info_request = self.create_request(self.user_info_url,
                                                          content_parser=self.adapter.json_parser,
                                                          response_parser=response_parser)
        
        return self._user_info_request
    
    
    @staticmethod
    def _credentials_parser(credentials, data):
        """
        Override this to handle differences in naming conventions of providers.
        
        :param credentials: Instance of Credentials class
        :param data: Response data dictionary
        """
        return credentials
    
    
    def update_user(self):
        return self.user_info_request.fetch().get_response().user
    

class AuthenticationProvider(BaseProvider):
    """Base class for OpenID providers."""
    
    identifier = ''
    
    def login(self, *args, **kwargs):
        """
        Launches the OpenID authentication procedure.
        
        Accepts oi_identifier optional parameter
        """
        
        # takes the oi_identifier argument into account only if the identifier is not hardcoded
        self.identifier = self.identifier or kwargs.get('oi_identifier', '')
        
        
        












