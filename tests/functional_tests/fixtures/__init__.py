# encoding: utf-8

from collections import namedtuple
import os
import pkgutil
import sys
import time

from jinja2 import (
    Environment,
    FileSystemLoader
)

from authomatic.providers import (
    oauth1,
    oauth2,
    openid,
)
from authomatic import six
from authomatic.six.moves import reload_module


# Add path of the functional_tests_path package to PYTHONPATH.
# This is necessary for the following imports to work when this module is
# imported from the expected_values.* modules.

FUNCTIONAL_TESTS_PATH = os.path.join(os.path.dirname(__file__), '..')
sys.path.append(FUNCTIONAL_TESTS_PATH)

from tests.functional_tests import expected_values

from tests.functional_tests import config


# Create template environment to load templates.
TEMPLATES_DIR = os.path.join(os.path.abspath(os.path.dirname(__file__)),
                             '..', 'templates')
env = Environment(loader=FileSystemLoader(TEMPLATES_DIR))

BIRTH_DATE_FORMAT = '%m-%d-%Y'
ASSEMBLED_CONFIG = {}
OAUTH2_PROVIDERS = {}
OAUTH1_PROVIDERS = {}
OPENID_PROVIDERS = {}


def render_home(framework_name):
    """
    Renders the homepage.
    """
    template = env.get_template('index.html')
    return template.render(providers=ASSEMBLED_CONFIG,
                           oauth2_providers=OAUTH2_PROVIDERS,
                           oauth1_providers=OAUTH1_PROVIDERS,
                           openid_providers=OPENID_PROVIDERS,
                           framework_name=framework_name)


def render_login_result(framework_name, result):
    """
    Renders the login handler.

    :param result:

        The :class:`.authomatic.core.LoginResult` returned by the
        :meth:`.authomatic.Authomatic.login` method.

    """

    reload_module(sys)
    if six.PY2:
        sys.setdefaultencoding('utf-8')

    response = None
    original_credentials = {}
    refreshed_credentials = {}
    if result:
        if result.user:
            result.user.update()
            if result.user.credentials:
                original_credentials.update(result.user.credentials.__dict__)
                time.sleep(2)
                response = result.user.credentials.refresh(force=True)
                refreshed_credentials.update(result.user.credentials.__dict__)

        user_properties = ['birth_date', 'city', 'country', 'email',
                           'first_name', 'gender', 'id', 'last_name', 'link',
                           'locale', 'location', 'name', 'nickname', 'phone',
                           'picture', 'postal_code', 'timezone', 'username']

        access_token_content = None
        if hasattr(result.provider, 'access_token_response'):
            access_token_content = result.provider.access_token_response.content

        template = env.get_template('login.html')
        return template.render(result=result,
                               providers=ASSEMBLED_CONFIG.values(),
                               oauth2_providers=OAUTH2_PROVIDERS,
                               oauth1_providers=OAUTH1_PROVIDERS,
                               openid_providers=OPENID_PROVIDERS,
                               user_properties=user_properties,
                               error=result.error,
                               credentials_response=response,
                               original_credentials=original_credentials,
                               refreshed_credentials=refreshed_credentials,
                               framework_name=framework_name,
                               access_token_content=access_token_content,
                               birth_date_format=BIRTH_DATE_FORMAT)


def get_configuration(provider):
    """
    Creates the user configuration which holds the tested values.

    It merges the ``config.COMMON`` and the ``config.PROVIDERS[provider]``
    dictionaries and returns a named tuple.

    :param str provider:
        Provider slug used in ``config.PROVIDERS``.

    :returns:

        A named tuple.

    """

    # Merge and override common settings with provider settings.
    conf = {}
    conf.update(config.COMMON)
    try:
        conf.update(config.PROVIDERS[provider])
    except KeyError:
        raise Exception('No record for the provider "{0}" was not found in the '
                        'config!'.format(provider))

    class_name = '{0}Configuration'.format(provider.capitalize())
    Res = namedtuple(class_name, sorted(conf.keys()))

    # Add additional class attributes which are not allowed to be passed
    # to the namedtuple
    Res.BIRTH_DATE_FORMAT = BIRTH_DATE_FORMAT
    bday = conf['user_birth_date']
    Res.user_birth_date_str = bday.strftime(Res.BIRTH_DATE_FORMAT)

    Res.no_birth_date = ['birth']
    Res.no_city = [conf['user_city'], 'city']
    Res.no_country = [conf['user_country'], 'country']
    Res.no_email = [conf['user_email'], 'email']
    Res.no_first_name = ['"{0}"'.format(conf['user_first_name']), 'first']
    Res.no_last_name = ['"{0}"'.format(conf['user_last_name']), 'last']
    Res.no_gender = [conf['user_gender'], 'gender']
    Res.no_link = ['link']
    Res.no_locale = [conf['user_locale'], 'language', 'locale']
    Res.no_nickname = ['nickname', conf['user_nickname']]
    Res.no_phone = [conf['user_phone'], 'phone']
    Res.no_picture = ['picture', 'avatar', 'image']
    Res.no_postal_code = [conf['user_postal_code'], 'postal', 'zip']
    Res.no_timezone = ['timezone']
    Res.no_username = ['username', '"{0}"'.format(conf['user_username'])]
    Res.no_location = [conf['user_country'], 'city',
                       'country', 'location'] + Res.no_postal_code + Res.no_city

    # Populate the namedtuple with provider settings.
    return Res(**conf)


expected_values_path = os.path.dirname(expected_values.__file__)

# Loop through all modules of the expected_values package
# except the _template.py
for importer, name, ispkg in pkgutil.iter_modules([expected_values_path]):
    # Import the module
    mod = importer.find_module(name).load_module(name)

    # Assemble result
    result = {}
    result.update(config.PROVIDERS[name])
    result.update(mod.CONFIG)

    result['_path'] = '{0}?id={1}'.format(name, result['openid_identifier']) \
        if result.get('openid_identifier') else name

    ASSEMBLED_CONFIG[name] = result
    if oauth2.OAuth2 in result['class_'].__mro__:
        OAUTH2_PROVIDERS[name] = result

    if oauth1.OAuth1 in result['class_'].__mro__:
        OAUTH1_PROVIDERS[name] = result

    if openid.OpenID in result['class_'].__mro__:
        OPENID_PROVIDERS[name] = result
