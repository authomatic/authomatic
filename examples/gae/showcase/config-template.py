# -*- coding: utf-8 -*-
"""
Keys with leading underscore are our custom provider-specific data.
"""

from authomatic.providers import oauth2, oauth1, openid, gaeopenid
import authomatic
import copy

DEFAULT_MESSAGE = 'Have you got a bandage?'

SECRET = '##########'

DEFAULTS = {
    'popup': True,
}

AUTHENTICATION = {
    'openid': {
        'class_': openid.OpenID,
    },
    'gae-openid': {
        'class_': gaeopenid.GAEOpenID,
    },
}

OAUTH1 = {
    'bitbucket': {
        'class_': oauth1.Bitbucket,
        'consumer_key': '##########',
        'consumer_secret': '##########',
        'id': authomatic.provider_id(),
        '_apis': {
            'Get repos you follow': ('GET', 'https://api.bitbucket.org/1.0/user/repositories/overview'),
            'Get your privileges': ('GET', 'https://api.bitbucket.org/1.0/user/privileges'),
        }
    },

    'flickr': {
        'class_': oauth1.Flickr,
        'consumer_key': '##########',
        'consumer_secret': '##########',
        'id': authomatic.provider_id(),
        '_apis': {
            'List your photos': ('GET', 'http://api.flickr.com/services/rest?method=flickr.activity.userPhotos&format=json'),
            'List your comments': ('GET', 'http://api.flickr.com/services/rest?method=flickr.activity.userComments&format=json'),
        },
    },

    'meetup': {
        'class_': oauth1.Meetup,
        'consumer_key': '##########',
        'consumer_secret': '##########',
        'id': authomatic.provider_id(),
    },

    'plurk': {
        'class_': oauth1.Plurk,
        'consumer_key': '##########',
        'consumer_secret': '##########',
        'id': authomatic.provider_id(),
        '_apis': {
            'Get your plurks': ('GET', 'http://www.plurk.com/APP/Timeline/getPlurks?filter=only_user'),
            'Plurk something': ('POST', 'http://www.plurk.com/APP/Timeline/plurkAdd?qualifier=says&content={message}'),
        }
    },

    'twitter': {
        'class_': oauth1.Twitter,
        'consumer_key': '##########',
        'consumer_secret': '##########',
        'id': authomatic.provider_id(),
        '_apis': {
            'Get your recent tweets': ('GET', 'https://api.twitter.com/1.1/statuses/user_timeline.json'),
            'Post a tweet': ('POST', 'https://api.twitter.com/1.1/statuses/update.json?status={message}', 'Message', 'Have you got a bandage?'),
        },
    },

    'tumblr': {
        'class_': oauth1.Tumblr,
        'consumer_key': '##########',
        'consumer_secret': '##########',
        'id': authomatic.provider_id(),
        '_apis': {
            'Get your likes': ('GET', 'https://api.tumblr.com/v2/user/likes'),
            'Follow': ('POST', 'https://api.tumblr.com/v2/user/follow?url={message}', 'Tumblr blog URL', 'peterhudec.tumblr.com'),
        },
    },

    'vimeo': {
        'class_': oauth1.Vimeo,
        'consumer_key': '##########',
        'consumer_secret': '##########',
        'id': authomatic.provider_id(),
        '_apis': {
            'Get your activity': ('GET', 'http://vimeo.com/api/rest/v2?method=vimeo.activity.happenedToUser&format=json&user_id={user.id}'),
        },
    },

    'xero': {
        'class_': oauth1.Xero,
        'consumer_key': '##########',
        'consumer_secret': '##########',
        'id': authomatic.provider_id(),
    },

    'xing': {
        'class_': oauth1.Xing,
        'consumer_key': '##########',
        'consumer_secret': '##########',
        'id': authomatic.provider_id(),
        '_icon': 'https://www.xing.com/favicon.ico',
        '_apis': {
            'Get job recommendations': ('GET', "https://api.xing.com/v1/users/{user.id}/jobs/recommendations"),
            'Get activity stream': ('GET', "https://api.xing.com/v1/users/{user.id}/feed"),
        },
    },

    'yahoo': {
        'class_': oauth1.Yahoo,
        'consumer_key': '##########--',
        'consumer_secret': '##########',
        'id': authomatic.provider_id(),
        '_apis': {
            'Get recent emails': ('GET', "http://query.yahooapis.com/v1/yql?q=select%20*%20from%20ymail.messages%20where%20numMid%3D'5'&format=json&securityLevel=user"),
        },
    },
}

OAUTH2 = {
    'amazon': {
        'class_': oauth2.Amazon,
        'consumer_key': '##########',
        'consumer_secret': '##########',
        'id': authomatic.provider_id(),
        'scope': oauth2.Amazon.user_info_scope,
    },

    # Behance doesn't support third party authorization anymore
    # 'behance': {
    #     'class_': oauth2.Behance,
    #     'consumer_key': '##########',
    #     'consumer_secret': '##########',
    #     'id': authomatic.provider_id(),
    #     'scope': oauth2.Behance.user_info_scope + ['post_as'],
    #     '_apis': {
    #         'Get your collections.': ('GET', 'http://behance.net/v2/users/{user.username}/collections'),
    #         'Get your statistics.': ('GET', 'http://behance.net/v2/users/{user.username}/stats'),
    #         'Follow a user.': ('POST', 'http://behance.net/v2/users/{message}/follow', 'Username or ID', 'peterhudec'),
    #     },
    # },

    'bitly': {
        'class_': oauth2.Bitly,
        'consumer_key': '##########',
        'consumer_secret': '##########',
        'id': authomatic.provider_id(),
        'scope': oauth2.Bitly.user_info_scope,
        '_apis': {
            'Get your link history': ('GET', 'https://api-ssl.bitly.com/v3/user/link_history'),
            'Shorten a URL': ('GET', 'https://api-ssl.bitly.com/v3/shorten?longUrl={message}', 'URL', 'http://peterhudec.com'),
        },
    },

    'cosm': {
        'class_': oauth2.Cosm,
        'consumer_key': '##########',
        'consumer_secret': '##########',
        'id': authomatic.provider_id(),
        'scope': oauth2.Cosm.user_info_scope,
    },

    'deviantart': {
        'class_': oauth2.DeviantART,
        'consumer_key': '##########',
        'consumer_secret': '##########',
        'id': authomatic.provider_id(),
        'scope': oauth2.DeviantART.user_info_scope,
    },

    'eventbrite': {
        'class_': oauth2.Eventbrite,
        'consumer_key': '##########',
        'consumer_secret': '##########',
        'id': authomatic.provider_id(),
        'scope': oauth2.Eventbrite.user_info_scope,
        '_apis': {
            'List your orders': ('GET', 'https://www.eventbriteapi.com/v3/users/{user.id}/orders/'),
            'List your owned events': ('GET', 'https://www.eventbriteapi.com/v3/users/{user.id}/owned_events/'),
            'Search for event': ('GET', 'https://www.eventbriteapi.com/v3/events/search/?q={message}', 'search string', 'Little Britain'),
        },
    },

    'facebook': {

        'class_': oauth2.Facebook,
        'consumer_key': '##########',
        'consumer_secret': '##########',
        'id': authomatic.provider_id(),
        'scope': oauth2.Facebook.user_info_scope + ['publish_stream'],
        '_apis': {
            'Get your recent statuses': ('GET', 'https://graph.facebook.com/{user.id}/feed'),
            'Share this page': ('POST', 'https://graph.facebook.com/{user.id}/feed?message={message}&link=http://authomatic-example.appspot.com',
                                'Enter comment', 'This app is ...'),
        },
    },

    'foursquare': {

        'class_': oauth2.Foursquare,
        'consumer_key': '##########',
        'consumer_secret': '##########',
        'id': authomatic.provider_id(),
        'scope': oauth2.Foursquare.user_info_scope,
        '_apis': {
            'Get your recent checkins': ('GET', 'https://api.foursquare.com/v2/users/{user.id}/checkins'),
            'Get your badges': ('GET', 'https://api.foursquare.com/v2/users/{user.id}/badges'),
        },
    },

    'github': {

        'class_': oauth2.GitHub,
        'consumer_key': '##########',
        'consumer_secret': '##########',
        'id': authomatic.provider_id(),
        'scope': oauth2.GitHub.user_info_scope,
        '_apis': {
            'Get your events': ('GET', 'https://api.github.com/users/{user.username}/events'),
            'Get your watched repos': ('GET', 'https://api.github.com/user/subscriptions'),
        },
    },

    'google': {
        'class_': oauth2.Google,
        'consumer_key': '##########',
        'consumer_secret': '##########',
        'id': authomatic.provider_id(),
        'scope': oauth2.Google.user_info_scope + [
            'https://www.googleapis.com/auth/calendar',
            'https://mail.google.com/mail/feed/atom',
            'https://www.googleapis.com/auth/drive',
            'https://gdata.youtube.com'],
        '_apis': {
            'List your calendars': ('GET', 'https://www.googleapis.com/calendar/v3/users/me/calendarList'),
            'List your YouTube playlists': ('GET', 'https://gdata.youtube.com/feeds/api/users/default/playlists?alt=json'),
        },
    },

    'linkedin': {
        'class_': oauth2.LinkedIn,
        'consumer_key': '##########',
        'consumer_secret': '##########',
        'id': authomatic.provider_id(),
        'scope': oauth2.LinkedIn.user_info_scope + ['rw_nus', 'r_network'],
        '_name': 'LinkedIn',
        '_apis': {
            'List your connections': ('GET', 'https://api.linkedin.com/v1/people/~/connections'),
        },
    },

    'paypal': {
        'class_': oauth2.PayPal,
        'consumer_key': '##########',
        'consumer_secret': '##########',
        'id': authomatic.provider_id(),
        'scope': oauth2.PayPal.user_info_scope,
        '_name': 'PayPal',
    },

    'reddit': {
        'class_': oauth2.Reddit,
        'consumer_key': '##########',
        'consumer_secret': '##########',
        'id': authomatic.provider_id(),
        'scope': oauth2.Reddit.user_info_scope,
    },

    # Viadeo doesn't support OAuth 2.0 API publicly anymore.
    # 'viadeo': {
    #     'class_': oauth2.Viadeo,
    #     'consumer_key': '##########',
    #     'consumer_secret': '##########',
    #     'id': authomatic.provider_id(),
    #     'scope': oauth2.Viadeo.user_info_scope,
    #     '_apis': {
    #         'Get your inbox': ('GET', 'https://api.viadeo.com/me/inbox'),
    #         'Get your newsfeed': ('GET', 'https://api.viadeo.com/me/home_newsfeed'),
    #         'Post a status': ('POST', 'https://api.viadeo.com/status?message={message}', 'Status', DEFAULT_MESSAGE),
    #     },
    # },

    'vk': {
        'class_': oauth2.VK,
        'consumer_key': '##########',
        'consumer_secret': '##########',
        'id': authomatic.provider_id(),
        'scope': oauth2.VK.user_info_scope + ['1026'],
        '_name': 'VK',
        '_apis': {
            'Get your history': ('GET', 'https://api.vk.com/method/activity.getHistory'),
            'Get your news': ('GET', 'https://api.vk.com/method/activity.getNews'),
            'Get your friends': ('GET', 'https://api.vk.com/method/friends.get'),
        },
    },

    'windows_live': {
        'class_': oauth2.WindowsLive,
        'consumer_key': '##########',
        'consumer_secret': '##########',
        'id': authomatic.provider_id(),
        'scope': oauth2.WindowsLive.user_info_scope + ['wl.skydrive'],
        '_name': 'Live',
        '_apis': {
            'List your recent documents': ('GET', 'https://apis.live.net/v5.0/me/skydrive/recent_docs'),
            'List your contacts': ('GET', 'https://apis.live.net/v5.0/me/contacts'),
        },
    },

    'yammer': {
        'class_': oauth2.Yammer,
        'consumer_key': '##########',
        'consumer_secret': '##########',
        'id': authomatic.provider_id(),
        'scope': oauth2.Yammer.user_info_scope,
        '_apis': {
            'Your feed': ('GET', 'https://www.yammer.com/api/v1/messages/my_feed.json'),
        },
    },

    'yandex': {
        'class_': oauth2.Yandex,
        'consumer_key': '##########',
        'consumer_secret': '##########',
        'id': authomatic.provider_id(),
        'scope': oauth2.Yandex.user_info_scope,
    },
}

# Concatenate the configs.
config = copy.deepcopy(OAUTH1)
config.update(OAUTH2)
config.update(AUTHENTICATION)
config['__defaults__'] = DEFAULTS
