import datetime
import logging
import simpleauth2

HTTP_METHODS = ('GET', 'HEAD', 'POST', 'PUT', 'DELETE', 'TRACE', 'OPTIONS', 'CONNECT', 'PATCH')

QUERY_STRING_PARSER = 'query_string_parser'
JSON_PARSER = 'json_parser'

class BaseProvider(object):
    """
    Base class for all providers
    """
    
    def __init__(self, adapter, provider_name, consumer, callback, short_name=None):
        self.provider_name = provider_name
        self.consumer = consumer
        self.callback = callback
        self.adapter = adapter
        self.short_name = short_name
        self.credentials = None
        
        self._user = None
        self._phase = None
                
        self._user_info_request = None
        
        # recreate full current URL
        self.uri = self.adapter.get_current_uri()
    
    
    #=======================================================================
    # Static properties to be overriden by subclasses
    #=======================================================================
    
    # tuple of URLs ordered by their usage
    urls = (None, )
    
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
        
    def login(self, **kwargs):
        pass
    
    
    #===========================================================================
    # Exposed methods
    #===========================================================================
    
    @classmethod
    def get_type(cls):
        return cls.__module__ + '.' + cls.__bases__[0].__name__
    
    @staticmethod
    def create_url(url_type, base):
        raise NotImplementedError
    
    
    def get_user(self):
        return self._user
    
    
    @property
    def phase(self):
        if self._phase is None:
            self._phase = self.adapter.get_phase(self.provider_name)
        return self._phase
    
    #===========================================================================
    # Internal methods
    #===========================================================================
    
    def _increase_phase(self):
        self.adapter.set_phase(self.provider_name, self.phase + 1)
    
    def _reset_phase(self):   
        self.adapter.set_phase(self.provider_name, 0)
    
    def _fetch(self, content_parser, url, params={}, method='GET', headers={}):
        #TODO: Check whether the method is valid
        if not method in HTTP_METHODS:
            raise simpleauth2.exceptions.HTTPError('The {} is not a valid HTTP method!'.format(method))
        
        return self.adapter.fetch_async(content_parser, url, params, method, headers).get_response()
    
    def _update_or_create_user(self, data):
        """
        Updates the properties of the self._user object.
        
        Takes into account the self.user_info_mapping property.
        """
        
        if not self._user:
            self._user = simpleauth2.User()
        
        self._user.raw_user_info = data
        
        # iterate over User properties
        for key in self._user.__dict__.keys():
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
                    setattr(self._user, key, new_value)
        
        return self._user
    
    
    def _update_credentials(self, data):
        
        self.credentials.access_token_secret = data.get('access_token_secret')
        self.credentials.expires_in = data.get('expires_in')
        
        return self.credentials
        
    
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
            raise simpleauth2.exceptions.ConfigError('Consumer key not specified for provider {}!'.format(self.provider_name))


class ProtectedResorcesProvider(BaseProvider):
    
    has_protected_resources = True
        
    
    @staticmethod
    def credentials_to_tuple(credentials):
        raise NotImplementedError
    
    
    @staticmethod
    def credentials_from_tuple(tuple_):
        raise NotImplementedError
    
    
    def fetch(self, url, parser=None):
        return self.create_request(url, parser=parser).fetch().get_response()
    
    
    def create_request(self, url, method='GET', content_parser=None, response_parser=None):       
        return simpleauth2.Request(adapter=self.adapter,
                       url=url,
                       credentials=self.credentials,
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
                user = self._update_or_create_user(response.data)
                return simpleauth2.UserInfoResponse(response, user)
            
            self._user_info_request = self.create_request(self.urls[-1],
                                                          content_parser=self.adapter.json_parser,
                                                          response_parser=response_parser)
        
        return self._user_info_request
    
    
    def get_user(self):
        self.user_info_request.fetch().get_response().user
    

class OpenIDBaseProvider(BaseProvider):
    
    def login(self, *args, **kwargs):
        self.identifier = kwargs.get('oi_identifier') or self.urls[0]
        
    
    # http://openid.net/specs/openid-attribute-properties-list-1_0-01.html
    AX_SCHEMAS = ('http://axschema.org/contact/email',
                  'http://schema.openid.net/contact/email',
                  'http://axschema.org/namePerson',
                  'http://openid.net/schema/namePerson/first',
                  'http://openid.net/schema/namePerson/last',
                  'http://openid.net/schema/gender',
                  'http://openid.net/schema/language/pref',
                  'http://openid.net/schema/contact/web/default',
                  'http://openid.net/schema/media/image',
                  'http://openid.net/schema/timezone',)
    
    # google requires this schema
    AX_SCHEMAS_REQUIRED = ('http://schema.openid.net/contact/email', )
    
    # http://openid.net/specs/openid-simple-registration-extension-1_1-01.html#response_format
    SREG_FIELDS = ('nickname',
                 'email',
                 'fullname',
                 'dob',
                 'gender',
                 'postcode',
                 'country',
                 'language',
                 'timezone')
    
    PAPE_POLICIES = ['http://schemas.openid.net/pape/policies/2007/06/multi-factor-physical',
                     'http://schemas.openid.net/pape/policies/2007/06/multi-factor',
                     'http://schemas.openid.net/pape/policies/2007/06/phishing-resistant',
                     'http://schemas.openid.net/pape/policies/2007/06/none']
    
    user_info_mapping = {
        'name': lambda data: data.get('sreg', {}).get('fullname') or \
                    data.get('ax', {}).get('http://axschema.org/namePerson'),
                             
        'first_name': lambda data: data.get('ax', {}).get('http://openid.net/schema/namePerson/first'),
                             
        'last_name': lambda data: data.get('ax', {}).get('http://openid.net/schema/namePerson/last'),
                             
        'user_id': lambda data: data.get('guid'),
                             
        'gender': lambda data: data.get('sreg', {}).get('gender') or \
                         data.get('ax', {}).get('http://openid.net/schema/gender'),
        
        'locale': lambda data: data.get('sreg', {}).get('language') or \
                         data.get('ax', {}).get('http://openid.net/schema/language/pref'),
        
        'link': lambda data: data.get('ax', {}).get('http://openid.net/schema/contact/web/default'),
        
        'picture': lambda data: data.get('ax', {}).get('http://openid.net/schema/media/image'),
        
        'timezone': lambda data: data.get('sreg', {}).get('timezone') or \
                           data.get('ax', {}).get('http://openid.net/schema/timezone'),
        
        'email': lambda data: data.get('sreg', {}).get('email') or \
                        data.get('ax', {}).get('http://axschema.org/contact/email') or \
                        data.get('ax', {}).get('http://schema.openid.net/contact/email'),
        
        'birth_date': lambda data: datetime.datetime.strptime(data.get('sreg', {}).get('dob'), '%Y-%m-%d') if data.get('sreg', {}).get('dob') else None,
        
        'nickname': lambda data: data.get('sreg', {}).get('nickname'),
        
        'country': lambda data: data.get('sreg', {}).get('country'),
        
        'postal_code': lambda data: data.get('sreg', {}).get('postcode'),
        
        
    }




