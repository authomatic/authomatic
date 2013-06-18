from django.http import HttpResponse
from authomatic import Authomatic
from authomatic.adapters import DjangoAdapter

from config import CONFIG

authomatic = Authomatic(CONFIG, 'abcdef', report_errors=None)

def index(request):
    return HttpResponse('Home')

def login(request, provider_name):
    
    response = HttpResponse()
    
    result = authomatic.login(DjangoAdapter(request, response), provider_name)
     
    if result:
        if result.error:
            response.write('Error {}'.format(result.error.message))    
        if result.user:
            result.user.update()
            response.write('Hi {}'.format(result.user.name))
    
    return response

