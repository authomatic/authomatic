$ = jQuery

log = (args...) ->
  if authomatic.defaults.logging
    console.log 'Authomatic:', args...


window.authomatic = new class Authomatic
  defaults:
    logging: on
    endpoint: null
    method: "GET"
    params: {}
    headers: {}
    substitute: {}
    beforeEndpoint: (jqXHR) ->
    afterEndpoint: (jqXHR) ->
    beforeSend: (jqXHR) ->
    success: (data, status, jqXHR) ->
    error: (jqXHR) ->
    done: (jqXHR) ->
  
  accessDefaults:
    backend: null
    substitute: {}
    beforeEndpoint: (jqXHR) ->
    afterEndpoint: (jqXHR) ->
    beforeSend: (jqXHR) ->
    success: (data, status, jqXHR) ->
    error: (jqXHR) ->
    done: (jqXHR) ->
  
  _openWindow: (url, width, height) ->
    top = (screen.height / 2) - (height / 2)
    left = (screen.width / 2) - (width / 2)
    settings = "width=#{width},height=#{height},top=#{top},left=#{left}"
    window.open(url, "authomatic:#{url}", settings)
  
  popup: (width = 800, height = 600, validator = (($form)-> true),
                    aSelector = 'a.authomatic', formSelector = 'form.authomatic') ->
    $(aSelector).click (e) =>
      e.preventDefault()
      @_openWindow(e.target.href, width, height)
    
    $(formSelector).submit (e) =>
      e.preventDefault()
      $form = $(e.target);
      url = $form.attr('action') + '?' + $form.serialize()
      if validator($form)
        @_openWindow(url, width, height)
  
  splitUrl: (url) ->
    url: url.substring(0, url.indexOf('?'))
    qs: url.substring(url.indexOf('?') + 1)
  
  parseQueryString: (queryString) ->
    result = {}
    for item in queryString.split('&')
      [k, v] = item.split('=')
      if result.hasOwnProperty k
        if Array.isArray result[k]
          result[k].push(v)
        else
          result[k] = [result[k], v]
      else
        result[k] = v
    result
  
  deserializeCredentials: (credentials) ->
    sc = decodeURIComponent(credentials).split('\n')
    id: parseInt(sc[0])
    type: parseFloat(sc[1])
    rest: sc[2..]
  
  getProviderClass: (credentials) ->
    type = @deserializeCredentials(credentials).type
    
    if type > 1 and type < 2
      Oauth1Provider
    
    else if type > 1 and type < 3
      # OAuth 2.0
      OAuth2JsonpProvider
    
    else
      BaseProvider
  
  access: (credentials, url, options) ->
    options = $.extend(authomatic.accessDefaults, options)
    
    url = @format(url, options.substitute)
    
    Provider = @getProviderClass(credentials)
    log("Instantiating #{Provider.name}.")
    provider = new Provider(options.backend, credentials, url, options)
    provider.access()
  
  format: (template, substitute) ->
    # Replace all {object.value} tags
    template.replace /{([^}]*)}/g, (match, tag)->
      # Traverse through dotted path in substitute
      target = substitute
      for level in tag.split('.')
        target = target[level]
      # Return value of the last object in the path
      target
  
  @jsonPCallbackCounter: 0
  
  addJsonpCallback: (callback) =>
    Authomatic.jsonPCallbackCounter += 1
    name = "jsonpCallback#{Authomatic.jsonPCallbackCounter}"
    path = "authomatic.#{name}"
    @[name] = (data) =>
      log('Calling jsonp callback:', path)
      callback?(data)
      log('Deleting jsonp callback:', path)
      delete @[name]
    log('Adding jsonp callback:', path)
    path

########################################################################################

# Providers with Access-Control-Allow-Origin: *
#
# Facebook
# Github
# Yahoo
# Foursquare
# 

# Yet to test
#
# Behance


class BaseProvider
  constructor: (@backend, @credentials, @url, options) ->
    defaults =
      method: 'GET'
      params: {}
      complete: (jqXHR, status) -> log('access complete', jqXHR, status)
      success: (data, status, jqXHR) -> log('access succeded', data, jqXHR, status)
    
    @options = $.extend(defaults, options)
    @deserializedCredentials = authomatic.deserializeCredentials(@credentials)
    @providerID = @deserializedCredentials.id
    @providerType = @deserializedCredentials.type
    @credentialsRest = @deserializedCredentials.rest
  
  contactBackend: (callback) =>
    data =
      credentials: @credentials
      url: @url
      method: @options.method
      params: @options.params
    
    log "Contacting backend at #{@backend}."
    $.get(@backend, data, callback)
  
  contactProvider: (requestElements) =>
    {url, method, params, headers, body} = requestElements
    
    params = authomatic.parseQueryString(body) if body
    
    @options['type'] = method
    @options['data'] = params
    @options['headers'] = headers
    
    log "Contacting provider.", url, @options
    $.ajax(url, @options)
      
  
  access: =>
    @contactBackend (data, textStatus, jqXHR) =>
      responseTo = jqXHR?.getResponseHeader 'Authomatic-Response-To'
      if responseTo is 'fetch'
        log "Fetch data returned from backend.", data
        @options.success(data, status, jqXHR)
        @options.complete(jqXHR, textStatus)
      else if responseTo is 'elements'
        log "Request elements data returned from backend.", data
        @contactProvider(data)

class Oauth1Provider extends BaseProvider

class Oauth1JsonpProvider extends Oauth1Provider
  # TODO: Implement Oauth1JsonpProvider
  # 1. Generate JSONP callback.
  # 2. Sign request elements at backend including JSONP callback.
  #   FIXME: Backend should allways return url and params separately
  # 3. Remove JSONP callback from request elements params
  # 4. Pass JSONP callback to jQuery.json

class Oauth2Provider extends BaseProvider
  constructor: (args...) ->
    super(args...)
    # Handle different naming conventions.
    @_x_unifyDifferences()
    # Unpack credentials elements.
    [@accessToken, @refreshToken, @expirationTime, @tokenType] = @credentialsRest
  
  _x_unifyDifferences: =>
    @_x_bearer = 'Bearer'
    @_x_accessToken = 'access_token'
  
  handlePOST: =>
    if @options.method in ['POST', 'PUT']
      # remove querystring from url, convert to dict and add to params
      {url, qs} = authomatic.splitUrl(@url)
      @params = $.extend(@options.params, authomatic.parseQueryString(qs))
  
  handleTokenType: =>
    if @tokenType is '1'
      # If token type is "1" which means "Bearer", pass access token in authorisation header
      @options.headers['Authorization'] = "#{@_x_bearer} #{accessToken}"
    else
      # Else pass it as querystring parameter
      @options.params[@_x_accessToken] = @accessToken
  
class OAuth2CrossDomainProvider extends Oauth2Provider
  access: =>
    @handlePOST()
    @handleTokenType()
    
    requestElements = 
      url: @url
      method: @options.method
      params: @options.params
      headers: @options.headers
    
    @contactProvider(requestElements)

class OAuth2JsonpProvider extends OAuth2CrossDomainProvider
  contactProvider: (requestElements) =>
    {url, method, params, headers, body} = requestElements
    
    params = authomatic.parseQueryString(body) if body
    
    @options.type = method
    @options.data = params
    @options.headers = headers
    
    @options.jsonpCallback = authomatic.addJsonpCallback(@options.success)
    # @options.cache = true
    # @options.dataType = 'jsonp'
    
    log "Contacting provider.", url, @options
    $.ajax(url, @options)


window.pokus = ->
  backend = 'http://authomatic.com:8080/json'
  
  twUrl = 'https://api.twitter.com/1.1/statuses/user_timeline.json'
  twCredentials = '5%0A1.5%0A1186245026-TI2YCrKLCsdXH7PeFE8zZPReKDSQ5BZxHzpjjel%0A1Xhim7w8N9rOs05WWC8rnwIzkSz1lCMMW9TSPLVtfk'
  
  fbUrl = 'https://graph.facebook.com/737583375/feed'
  fbCredentials = '15%0A2.5%0ABAAG3FAWiCwIBAJn0CKLOphV4meEbBvUcGcAXIN0z1Pv2JtCrziXlKvM99WX3p4YxI9oHC02ZCpsv7d3CZCsTMy9lqZAohaypwb3nGSKAscqngzFVTOULGLRd5ygXQYtqcka1iERfZAfZA8KQjx7Mps0izinhKyV0EGCJo1HhQcOjx1QYiCAEp%0A%0A1370766038%0A0'
  
  options =
    method: 'POST'
    params:
      message: 'keket'
    success: (data, status, jqXHR) -> log('hura, podarilo sa:', data)
      
  
  # provider = new OAuth2JsonpProvider(backend, fbCredentials, fbUrl, options)
  # provider.access()
  
  authomatic.accessDefaults.backend = 'http://authomatic.com:8080/json'
  authomatic.access(fbCredentials, fbUrl, options)

########################################################################################


window.cb = (data) ->
  console.log 'CALLBACK', data


    

