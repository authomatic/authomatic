# -*- coding: utf-8 -*-
# example/simple/urls.py

from django.conf.urls import patterns, url

import views

urlpatterns = patterns('',
                       url(r'^$', views.home, name='home'),
                       url(r'^login/(\w*)', views.login, name='login')
                       )
