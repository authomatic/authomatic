from authomatic.providers import oauth1, oauth2, openid, gaeopenid
import authomatic

PROVIDERS = {
             
    #===========================================================================
    # OAutht 2.0
    #===========================================================================
    'facebook': {
         'class_': oauth2.Facebook,
         'short_name': authomatic.short_name(),
         'consumer_key': '494017363953317',
         'consumer_secret': 'e20424639fcedddd68ff8e57add2d70d',
         'scope': ['user_about_me',
                   'email']
    },
    'google': {
         'class_': 'authomatic.providers.oauth2.Google',
         'short_name': authomatic.short_name(),
         'consumer_key': '121641813816.apps.googleusercontent.com',
         'consumer_secret': 'zPqoFD1AFcGTCr2d8dQkbEAw',
         'scope': ['https://www.googleapis.com/auth/userinfo.profile',
                   'https://www.googleapis.com/auth/userinfo.email']
    },
    'windows_live': {
         'class_': 'oauth2.WindowsLive',
         'short_name': authomatic.short_name(),
         'consumer_key': '00000000480E36E2',
         'consumer_secret': 'f3lkeZBAQqmn7nzs4aS5IadVBDxW3o19',
         'scope': ['wl.basic',
                   'wl.emails',
                   'wl.photos']
    },
    
    #===========================================================================
    # OAuth 1.0
    #===========================================================================
    'twitter': {
         'class_': oauth1.Twitter,
         'short_name': authomatic.short_name(),
         'consumer_key': '5H31GA4khCEePaWnXoE1ig',
         'consumer_secret': 'Bp2Ikj4sQSOBQI8ZzsVcJGCxQ2wLIrThGmbI5IEH2g'
    },
             
    #===========================================================================
    # Open ID
    #===========================================================================
    
    'gaeoi': {
         'class_': gaeopenid.GAEOpenID,
         'identifier': 'https://me.yahoo.com',
    },             
    'oi': {
         'class_': openid.OpenID,
    },             
    'yoi': {
         'class_': openid.Yahoo,
    },             
    'goi': {
         'class_': openid.Google,
    }
}
