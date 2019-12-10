from django.http import HttpResponse
from django.shortcuts import render_to_response
from django.core.urlresolvers import reverse


def home(request):
    # Create links and OpenID form to the Login handler.
    simple_example_url = reverse('simple:home')

    return render_to_response('home.html', {})
