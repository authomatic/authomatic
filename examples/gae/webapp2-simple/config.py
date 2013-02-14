from authomatic.providers import oauth1, oauth2, openid, gaeopenid
import authomatic

PROVIDERS = {
    #===========================================================================
    # OAutht 2.0
    #===========================================================================
    'facebook': {
         'short_name': authomatic.short_name(),
         'class_name': oauth2.Facebook,
         'consumer_key': '494017363953317',
         'consumer_secret': 'e20424639fcedddd68ff8e57add2d70d',
         'scope': ['user_about_me',
                   'email']
    },
    'google': {
         'short_name': authomatic.short_name(),
         'class_name': 'authomatic.providers.oauth2.Google',
         'consumer_key': '121641813816.apps.googleusercontent.com',
         'consumer_secret': 'zPqoFD1AFcGTCr2d8dQkbEAw',
         'scope': ['https://www.googleapis.com/auth/userinfo.profile',
                   'https://www.googleapis.com/auth/userinfo.email']
    },
    'windows_live': {
         'short_name': authomatic.short_name(),
         'class_name': 'oauth2.WindowsLive',
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
         'short_name': authomatic.short_name(),
         'class_name': oauth1.Twitter,
         'consumer_key': '5H31GA4khCEePaWnXoE1ig',
         'consumer_secret': 'Bp2Ikj4sQSOBQI8ZzsVcJGCxQ2wLIrThGmbI5IEH2g'
    },
             
    #===========================================================================
    # Open ID
    #===========================================================================
    
    'gaeoi': {
         'class_name': gaeopenid.GAEOpenID,
         'identifier': 'https://me.yahoo.com',
    },             
    'oi': {
         'class_name': openid.OpenID,
    },             
    'yoi': {
         'class_name': openid.Yahoo,
    },             
    'goi': {
         'class_name': openid.Google,
    }
}
