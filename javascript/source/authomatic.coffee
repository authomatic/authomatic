$ = jQuery

###########################################################
# Internal functions
###########################################################

log = (args...) ->
  if authomatic.defaults.logging
    console.log 'Authomatic:', args...

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
    Oauth1Provider
  else if type is 2
    OAuth2JsonpProvider
  else
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


###########################################################
# Global objects
###########################################################

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
  
  access: (credentials, url, options) ->
    options = $.extend(authomatic.accessDefaults, options)
    
    url = format(url, options.substitute)
    
    Provider = getProviderClass(credentials)
    log("Instantiating #{Provider.name}.")
    provider = new Provider(options.backend, credentials, url, options)
    provider.access()

  
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
  constructor: (@backend, @credentials, url, options) ->
    defaults =
      method: 'GET'
      params: {}
      complete: (jqXHR, status) -> log('access complete', jqXHR, status)
      success: (data, status, jqXHR) -> log('access succeded', data, jqXHR, status)
    
    options = $.extend(defaults, options)
    
    @deserializedCredentials = deserializeCredentials(@credentials)
    @providerID = @deserializedCredentials.id
    @providerType = @deserializedCredentials.type
    @credentialsRest = @deserializedCredentials.rest

    parsedUrl = parseUrl(url)
    @url = parsedUrl.url
    @method = options.method
    @params = $.extend(parsedUrl.params, options.params)

    @completeCallback = options.complete
    @successCallback = options.success
  
  contactBackend: (callback) =>
    data =
      credentials: @credentials
      url: @url
      method: @method
      params: JSON.stringify(@params)
    
    log "Contacting backend at #{@backend}.", data
    $.get(@backend, data, callback)
  
  contactProvider: (requestElements) =>
    {url, method, params, headers} = requestElements
    
    options =
      type: method
      data: params
      headers: headers
      complete: @completeCallback
      success: @successCallback
    
    log "Contacting provider.", url, options
    $.ajax(url, options)
  
  access: =>
    callback = (data, textStatus, jqXHR) =>
      # Find out whether backend returned fetch result or request elements.
      responseTo = jqXHR?.getResponseHeader('Authomatic-Response-To')

      if responseTo is 'fetch'
        log "Fetch data returned from backend.", data
        @successCallback(data, status, jqXHR)
        @completeCallback(jqXHR, textStatus)

      else if responseTo is 'elements'
        log "Request elements data returned from backend.", data
        @contactProvider(data)

      else
        log "WTF.", data, textStatus, jqXHR
    
    @contactBackend(callback)


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
    success: (data, status, jqXHR) -> log('hura, podarilo sa:', data)

  # Facebook
  fbUrl = 'https://graph.facebook.com/737583375/feed'
  fbCredentials = '15%0A2-5%0ABAAG3FAWiCwIBAJn0CKLOphV4meEbBvUcGcAXIN0z1Pv2JtCrziXlKvM99WX3p4YxI9oHC02ZCpsv7d3CZCsTMy9lqZAohaypwb3nGSKAscqngzFVTOULGLRd5ygXQYtqcka1iERfZAfZA8KQjx7Mps0izinhKyV0EGCJo1HhQcOjx1QYiCAEp%0A%0A1370766038%0A0'
  
  
  log('POKUS', parseUrl('http://example.com/foo/bar?a=1&b=2&c=3&b=4&d=%3F%2F%24%26'))
  
  # provider = new OAuth2JsonpProvider(backend, fbCredentials, fbUrl, options)
  # provider.access()
  
  authomatic.accessDefaults.backend = 'http://authomatic.com:8080/json'
  authomatic.access(twCredentials, twPostUrl, twPostOptions)

########################################################################################


window.cb = (data) ->
  console.log 'CALLBACK', data


    

