import authomatic
from fastapi import FastAPI
from fastapi.responses import PlainTextResponse
from authomatic.adapters import DjangoAdapter
from tests.functional_tests import fixtures

authomatic = authomatic.Authomatic(fixtures.ASSEMBLED_CONFIG, secret='123',
                                   report_errors=False)

app = FastAPI()


@app.get('/')
def home(request):
    return fixtures.render_home('django')


@app.route('/login/{provider_name}', methods=['GET', 'POST'])
def login(request, provider_name):
    response = PlainTextResponse()
    result = authomatic.login(DjangoAdapter(request, response), provider_name)

    if result:
        return fixtures.render_login_result('django', result)

    return response