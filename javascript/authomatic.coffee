$ = jQuery

jsonPCallbackCounter = 0

globalOptions =
  logging: on
  popupWidth: 800
  pupupHeight: 600
  backend: null
  substitute: {}
  params: {}
  headers: {}
  body: ''
  jsonpCallbackPrefix: 'authomaticJsonpCallback'
  beforeBackend: null
  backendComplete: null
  success: null
  complete: null


###########################################################
# Internal functions
###########################################################

log = (args...) ->
  console?.log 'Authomatic:', args... if globalOptions.logging

parseQueryString = (queryString) ->
  result = {}
  for item in queryString.split('&')
    [k, v] = item.split('=')
    v = decodeURIComponent(v)
    if result.hasOwnProperty k
      if Array.isArray result[k]
        result[k].push(v)
      else
        result[k] = [result[k], v]
    else
      result[k] = v
  result

parseUrl = (url) ->
  log('parseUrl', url)
  questionmarkIndex = url.indexOf('?')
  if questionmarkIndex >= 0
    u = url.substring(0, questionmarkIndex)
    qs = url.substring(questionmarkIndex + 1)
  else
    u = url

  url: u
  query: qs
  params: parseQueryString(qs) if qs

deserializeCredentials = (credentials) ->
  sc = decodeURIComponent(credentials).split('\n')

  typeId = sc[1]
  [type, subtype] = typeId.split('-')

  id: parseInt(sc[0])
  typeId: typeId
  type: parseInt(type)
  subtype: parseInt(subtype)
  rest: sc[2..]

getProviderClass = (credentials) ->
  {type, subtype} = deserializeCredentials(credentials)
  
  if type is 1
    # OAuth 1.0a providers.
    Oauth1Provider
  else if type is 2
    # OAuth 2 providers.
    if subtype is 6
      # Foursquare needs special treatment.
      Foursquare
    if subtype is 8
      # So does Google.
      Google
    else if subtype is 9
      # And so does LinkedIn.
      LinkedIn
    else if subtype is 12
      # Viadeo supports neither CORS nor JSONP.
      BaseProvider
    else
      Oauth2Provider
  else
    # Base provider allways works.
    BaseProvider

format = (template, substitute) ->
  # Replace all {object.value} tags
  template.replace /{([^}]*)}/g, (match, tag)->
    # Traverse through dotted path in substitute
    target = substitute
    for level in tag.split('.')
      target = target[level]
    # Return value of the last object in the path

    # TODO: URL encode
    target

# TODO: Not needed anymore
addJsonpCallback = (localSuccessCallback) =>
  Authomatic.jsonPCallbackCounter += 1
  name = "#{globalOptions.jsonpCallbackPrefix}#{Authomatic.jsonPCallbackCounter}"
  path = "window.#{name}"
  window[name] = (data) =>
    log('Calling jsonp callback:', path)
    globalOptions.success(data)
    localSuccessCallback?(data)
    log('Deleting jsonp callback:', path)
    delete @[name]
  log("Adding #{path} jsonp callback")
  name

###########################################################
# Global objects
###########################################################

window.authomatic = new class Authomatic
  @jsonPCallbackCounter: 0
  
  setup: (options) ->
    $.extend(globalOptions, options)
    log 'Setting up authomatic to:', globalOptions
  
  _openWindow: (url, width, height) ->
    top = (screen.height / 2) - (height / 2)
    left = (screen.width / 2) - (width / 2)
    settings = "width=#{width},height=#{height},top=#{top},left=#{left}"
    window.open(url, "authomatic:#{url}", settings)
  
  popup: (width = 800, height = 600, validator = (($form)-> true), aSelector = 'a.authomatic', formSelector = 'form.authomatic') ->
    $(aSelector).click (e) =>
      e.preventDefault()
      @_openWindow(e.target.href, width, height)
    
    $(formSelector).submit (e) =>
      e.preventDefault()
      $form = $(e.target);
      url = $form.attr('action') + '?' + $form.serialize()
      if validator($form)
        @_openWindow(url, width, height)
  
  access: (credentials, url, options = {}) ->
    localEvents =
      beforeBackend: null
      backendComplete: null
      success: null
      complete: null

    # Merge options with global options and local events
    updatedOptions = {}
    $.extend(updatedOptions, globalOptions, localEvents, options)

    # Format url.
    url = format(url, updatedOptions.substitute)
    
    log 'access options', updatedOptions, globalOptions

    Provider = getProviderClass(credentials)
    provider = new Provider(options.backend, credentials, url, updatedOptions)
    log 'Instantiating provider:', provider
    provider.access()


########################################################################################



class BaseProvider
  constructor: (@backend, @credentials, url, @options) ->
    @backendRequestType = 'auto'
    @jsonpRequest = no
    @jsonpCallbackName = "#{globalOptions.jsonpCallbackPrefix}#{jsonPCallbackCounter}"

    # Credentials
    @deserializedCredentials = deserializeCredentials(@credentials)
    @providerID = @deserializedCredentials.id
    @providerType = @deserializedCredentials.type
    @credentialsRest = @deserializedCredentials.rest

    # Request elements
    parsedUrl = parseUrl(url)
    @url = parsedUrl.url
    @params = {}
    $.extend(@params, parsedUrl.params, @options.params)
  
  contactBackend: (callback) =>
    if @jsonpRequest and @options.method is not 'GET'
      @backendRequestType = 'fetch'

    data =
      type: @backendRequestType
      credentials: @credentials
      url: @url
      method: @options.method
      body: @options.body
      params: JSON.stringify(@params)
      headers: JSON.stringify(@options.headers)
    
    globalOptions.beforeBackend?(data)
    @options.beforeBackend?(data)
    log "Contacting backend at #{@options.backend}.", data
    $.get(@options.backend, data, callback)
  
  contactProvider: (requestElements) =>
    {url, method, params, headers, body} = requestElements

    # Try cross domain request first.
    options =
      type: method
      data: params
      headers: headers
      complete: [
        ((jqXHR, textStatus) -> log 'Request complete.', textStatus, jqXHR)
        globalOptions.complete
        @options.complete
      ]
      success: [
        ((data) -> log 'Request successfull.', data)
        globalOptions.success
        @options.success
      ]
      error: (jqXHR, textStatus, errorThrown) =>
        # If cross domain fails,
        if jqXHR.state() is 'rejected'
          if @options.method is 'GET'
            log 'Cross domain request failed! trying JSONP request.'
            # access again but with JSONP request type.
            @jsonpRequest = yes
          else
            @backendRequestType = 'fetch'
          @access()

    if @jsonpRequest
      # Add JSONP arguments to options
      jsonpOptions =
        jsonpCallback: @jsonpCallbackName
        cache: true # If false, jQuery would add a nonce to query string which would break signature.
        dataType: 'jsonp'
        error: (jqXHR, textStatus, errorThrown) ->
          # If JSONP fails, there is not much to do.
          log 'JSONP failed! State:', jqXHR.state()
      $.extend(options, jsonpOptions)
      log "Contacting provider with JSONP request.", url, options
    else
      log "Contacting provider with cross domain request", url, options
    
    $.ajax(url, options)
  
  access: =>
    log 'ACCESSS'
    callback = (data, textStatus, jqXHR) =>
      # Call backend complete callbacks.
      globalOptions.backendComplete?(data, textStatus, jqXHR)
      @options.backendComplete?(data, textStatus, jqXHR)

      # Find out whether backend returned fetch result or request elements.
      responseTo = jqXHR?.getResponseHeader('Authomatic-Response-To')

      if responseTo is 'fetch'
        log "Fetch data returned from backend.", jqXHR.getResponseHeader('content-type'), data
        # Call success and complete callbacks manually.
        globalOptions.success?(data)
        @options.success?(data)
        globalOptions.complete?(jqXHR, textStatus)
        @options.complete?(jqXHR, textStatus)

      else if responseTo is 'elements'
        log "Request elements data returned from backend.", data
        @contactProvider(data)

    # Increase JSONP callback counter for next JSONP request.
    jsonPCallbackCounter += 1 if @jsonpRequest
    @contactBackend(callback)


class Oauth1Provider extends BaseProvider
  access: () ->
    @jsonpRequest = yes
    # Add JSONP callback name to params to be included in the OAuth 1.0a signature
    $.extend(@params, callback: @jsonpCallbackName)
    super()
    
  contactProvider: (requestElements) =>
    # We must remove the JSONP callback from params, because jQuery will add it too and
    # the OAuth 1.0a signature would not be valid if there are two callback params in the querystring.
    delete requestElements.params.callback
    super(requestElements)


class Oauth2Provider extends BaseProvider

  _x_accessToken: 'access_token'
  _x_bearer: 'Bearer'

  constructor: (args...) ->
    super(args...)
    
    # Unpack credentials elements.
    [@accessToken, @refreshToken, @expirationTime, @tokenType] = @credentialsRest

    # Handle token type.
    if @tokenType is '1'
      # If token type is "1" which means "Bearer", pass access token in authorisation header
      @options.headers['Authorization'] = "#{@_x_bearer} #{@accessToken}"
    else
      # Else pass it as querystring parameter
      @params[@_x_accessToken] = @accessToken

  access: () =>
    if @backendRequestType is 'fetch'
      super()
    else
      # Skip backend and go directly to provider.
      requestElements =
        url: @url
        method: @options.method
        params: @params
        headers: @options.headers
        body: @options.body

      @contactProvider(requestElements)


class Foursquare extends Oauth2Provider
  _x_accessToken: 'oauth_token'

class Google extends Oauth2Provider
  _x_bearer: 'OAuth'

class LinkedIn extends Oauth2Provider
  _x_accessToken: 'oauth2_access_token'



window.pokus = ->
  # Twitter
  twCredentials = '5%0A1-5%0A1186245026-TI2YCrKLCsdXH7PeFE8zZPReKDSQ5BZxHzpjjel%0A1Xhim7w8N9rOs05WWC8rnwIzkSz1lCMMW9TSPLVtfk'
  
  twPostUrl = 'https://api.twitter.com/1.1/statuses/update.json'
  twPostOptions =
    method: 'POST'
    params:
      status: 'keket'
    success: (data, status, jqXHR) -> log('hura, podarilo sa:', data)

  twGetUrl = 'https://api.twitter.com/1.1/statuses/user_timeline.json'
  twGetOptions =
    method: 'GET'
    params:
      pokus: 'POKUS'
    success: (data, status, jqXHR) -> log('hura, podarilo sa:', data)

  # Facebook
  fbUrl = 'https://graph.facebook.com/737583375/feed'
  fbCredentials = '15%0A2-5%0ABAAG3FAWiCwIBAJn0CKLOphV4meEbBvUcGcAXIN0z1Pv2JtCrziXlKvM99WX3p4YxI9oHC02ZCpsv7d3CZCsTMy9lqZAohaypwb3nGSKAscqngzFVTOULGLRd5ygXQYtqcka1iERfZAfZA8KQjx7Mps0izinhKyV0EGCJo1HhQcOjx1QYiCAEp%0A%0A1370766038%0A0'
  
  # Behance
  beCredentials = '11%0A2-1%0AN.W7MpNX5nTCgfwG3HLJTlc2KIZP5VMp%0A%0A0%0A0'
  beURL = 'http://behance.net/v2/collections/6870767/follow'

  # LinkedIn
  liCredentials = '19%0A2-9%0AAQVK822aqXqSUjScKzJJ-4ErqXT1OHvmEjcaX2OUNRtXdjFAsWbOUjnqzQYeiyztWjCenEXV3aNvTOVgrrpm0eoXxIUHbcr8qhsT5o9LCo5Molecguf6YPc9UHYWMOO_1kZ_eLO0M805f5GMYs4zGw8GyyCw6ATNRk6TlLECAt-od8Tu-S4%0A%0A0%0A0'
  liURL = 'https://api.linkedin.com/v1/people/~/shares'

  authomatic.setup(backend: 'http://authomatic.com:8080/login/')

  # authomatic.access liCredentials, liURL,
  #   method: 'POST'
  #   headers:
  #     'x-li-format': 'json'
  #     'content-type': 'application/json'
  #   body:
  #     JSON.stringify
  #       comment: 'Pokus'
  #       content:
  #         title: 'Ebenci'
  #         "submitted-url": "http://peterhudec.com"
  #       visibility:
  #         code: 'anyone'
  #   success: (data, status, jqXHR) ->
  #     log('VYSLEDOK:', data, status, jqXHR)

########################################################################################


window.cb = (data) ->
  console.log 'CALLBACK', data

# @ sourceMappingURL=authomatic.map