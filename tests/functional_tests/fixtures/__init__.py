from os import path

from jinja2 import Environment, FileSystemLoader


TEMPLATES_DIR = path.join(path.abspath(path.dirname(__file__)), '../templates')
env = Environment(loader=FileSystemLoader(TEMPLATES_DIR))


def render_home(config):
    template = env.get_template('index.html')
    return template.render(providers=config.PROVIDERS.keys())


def render_login_result(result, config):
    response = None
    if result:
        response_message = ''
        if result.user:
            result.user.update()
            if result.user.credentials:
                response = result.user.credentials.refresh(force=True)

        user_properties = config.PROVIDERS.values()[0]['user'].keys()

        template = env.get_template('login.html')

        return template.render(result=result,
                               providers=config.PROVIDERS.keys(),
                               user_properties=user_properties,
                               error=result.error,
                               credentials_response=response)
