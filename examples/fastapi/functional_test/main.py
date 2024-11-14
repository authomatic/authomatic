import authomatic
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, PlainTextResponse
from authomatic.adapters import FastAPIAdapter
from tests.functional_tests import fixtures

authomatic = authomatic.Authomatic(fixtures.ASSEMBLED_CONFIG, secret='123',
                                   report_errors=False)

app = FastAPI()


@app.get('/')
def home(request: Request):
    return HTMLResponse(fixtures.render_home('fastapi'))


@app.api_route('/login/{provider_name}', methods=['GET', 'POST'])
def login(request: Request, provider_name):
    response = PlainTextResponse()
    result = authomatic.login(FastAPIAdapter(request, response), provider_name)

    if result:
        return fixtures.render_login_result('fastapi', result)

    return response
