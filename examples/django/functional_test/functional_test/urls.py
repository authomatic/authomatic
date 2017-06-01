# -*- coding: utf-8 -*-
from django.conf.urls import patterns, include, url


urlpatterns = patterns('',
                       url(r'^$', 'functional_test.views.home', name='home'),
                       url(r'^login/(?P<provider_name>\w+)',
                           'functional_test.views.login', name='login'),
                       )
