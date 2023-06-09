from fastapi import Request, FastAPI
from fastapi.responses import JSONResponse
from authomatic.adapters import FastAPIAdapter
from authomatic import Authomatic
from config import CONFIG

authomatic = Authomatic(config=CONFIG, secret='YOUR SUPER CONFIDENTIAL SECRET')
app = FastAPI()


@app.get('/')
async def home():
    return 'Welcome home, why are you late?'


@app.api_route('/login/{provider}', methods=['GET', 'POST'])
async def login(request: Request, provider: str):
    """
    There's much repetitive code, but it's just a demonstration.
    """

    response = JSONResponse()
    result = authomatic.login(FastAPIAdapter(request, response), provider)

    if result:
        if result.error:
            return {
                'error': result.error.message
            }

        elif result.user:
            if not (result.user.name and result.user.id):
                result.user.update()

            user = result.user
            provider = result.provider

            if user:
                if provider.name == 'google':
                    response.body += 'You\'re now logged in with Google.<br />'.encode('utf-8')

                    provider_response = provider.access(
                        user.credentials,
                        'https://www.googleapis.com/oauth2/v1/userinfo?alt=json'
                    )

                    if provider_response.status == 200:
                        response.body += 'Hello {}'.format(provider_response['data'].name).encode('utf-8')


                if provider.name == 'github':
                    response.body += 'You\'re now logged in with GitHub.<br />'.encode('utf-8')

                    provider_response = provider.access('https://api.github.com/user', headers={
                        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'
                                      ' AppleWebKit/537.36 (KHTML, like Gecko) Chrome/92.0.4515.131 Safari/537.36'
                    })

                    if provider_response.status == 200:
                        response.body += 'Hello {}'.format(provider_response.data['name']).encode('utf-8')


    return response
