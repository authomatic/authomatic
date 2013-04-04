$ = jQuery

popup = (url, width, height)->
  top = (screen.height / 2) - (height / 2)
  left = (screen.width / 2) - (width / 2)
  settings = "width=#{width},height=#{height},top=#{top},left=#{left}"
  window.open(url, "authomatic:#{url}", settings)

authomatic = ->

authomatic.popup = (width = 800, height = 600, validator = (($form)-> true),
                    aSelector = 'a.authomatic', formSelector = 'form.authomatic')->
  $(aSelector).click (e)->
    e.preventDefault()
    popup(this.href, width, height)
  
  $(formSelector).submit (e)->
    e.preventDefault()
    $form = $(this);
    url = $form.attr('action') + '?' + $form.serialize()
    if validator($form)
      popup(url, width, height)
  
$.fn.authomatic = authomatic


