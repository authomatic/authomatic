# -*- coding: utf-8 -*-
from django.http import HttpResponse

import authomatic
from authomatic.adapters import DjangoAdapter
from tests.functional_tests import fixtures


authomatic = authomatic.Authomatic(fixtures.ASSEMBLED_CONFIG, secret='123',
                                   report_errors=False)


def home(request):
    return HttpResponse(fixtures.render_home('django'))


def login(request, provider_name):
    response = HttpResponse()
    result = authomatic.login(DjangoAdapter(request, response), provider_name)

    if result:
        return HttpResponse(fixtures.render_login_result('django',
                                                         result).encode())

    return response
