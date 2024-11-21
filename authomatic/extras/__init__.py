# -*- coding: utf-8 -*-

def get_diagnosis_info(result):
    """
    Get additional info about login.
    
    :attr result:
        = authomatic.login().
    """
    res = None
    # check email possibility for Facebook
    if result.provider.name == "facebook":
        provider = result.provider
        perm_url = provider.user_info_url + "/permissions"
        response = provider._fetch(perm_url, params={'access_token': provider.credentials.token})

        res = {
            "perm_url": perm_url,
            "status":   response.status,
            #"content":  response.content
            "content":  response.data
        }
        
    return res
