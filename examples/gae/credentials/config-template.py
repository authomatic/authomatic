# config.py

from authomatic.providers import oauth2, oauth1, openid, gaeopenid
import authomatic

CONFIG = {
    "tw": {  # Your internal provider name
        # Provider class
        "class_": oauth1.Twitter,
        # Twitter is an AuthorizationProvider so we need to set several other
        # properties too:
        "consumer_key": "####################",
        "consumer_secret": "####################",
        "id": authomatic.provider_id(),
    },
    "fb": {
        "class_": oauth2.Facebook,
        # Facebook is AuthorizationProvider too.
        "consumer_key": "####################",
        "consumer_secret": "####################",
        "id": authomatic.provider_id(),
        # We need the "publish_stream" scope to post to users timeline,
        # the "offline_access" scope to be able to refresh credentials,
        # and the other scopes to get user info.
        "scope": ["publish_stream", "offline_access", "user_about_me", "email"],
    },
    "gae_oi": {
        # OpenID provider based on Google App Engine Users API.
        # Works only on GAE and returns only the id and email of a user.
        # Moreover, the id is not available in the development environment!
        "class_": gaeopenid.GAEOpenID,
    },
    "oi": {
        # OpenID provider based on the python-openid library.
        # Works everywhere, is flexible, but requires more resources.
        "class_": openid.OpenID,
        "store": openid.SessionOpenIDStore,
    },
}
