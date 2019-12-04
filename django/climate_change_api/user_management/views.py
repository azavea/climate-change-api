"""Customized version of Django-registration plug-in's HMAC implementation.

A two-step (registration followed by activation) workflow, implemented by emailing an HMAC-verified
timestamped activation token to the user on signup.
"""

import json
import logging
import requests
import urllib

from django.conf import settings
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import HttpResponseRedirect, HttpResponse, JsonResponse
from django.shortcuts import render
from django.urls import reverse
from django.utils.cache import patch_vary_headers
from django.views.generic import View

from corsheaders.defaults import default_headers as default_cors_headers
from corsheaders.middleware import (ACCESS_CONTROL_ALLOW_CREDENTIALS,
                                    ACCESS_CONTROL_ALLOW_HEADERS,
                                    ACCESS_CONTROL_ALLOW_ORIGIN,
                                    ACCESS_CONTROL_EXPOSE_HEADERS)
from django_registration.backends.activation.views import RegistrationView as BaseRegistrationView
from rest_framework.authtoken.models import Token
from rest_framework.authtoken.views import ObtainAuthToken
from rest_framework.authentication import SessionAuthentication, TokenAuthentication
from rest_framework.permissions import IsAuthenticated, SAFE_METHODS
from rest_framework.response import Response

from user_management.forms import UserForm, UserProfileForm
from user_management.models import UserProfile
from user_management.throttling import ObtainAuthTokenThrottle
from user_management.serializers import AuthTokenSerializer


logger = logging.getLogger(__name__)


def _post_hubspot_lead(request, user):
    """Register new external users to HubSpot."""
    if user.email.endswith(settings.COMPANY_DOMAIN):
        return

    hs_context = {}
    if 'hubspotutk' in request.COOKIES:
        hs_context['hutk'] = request.COOKIES['hubspotutk']
    # If we're in production, this header should have the original IP
    if 'HTTP_X_FORWARDED_FOR' in request.META:
        hs_context['ipAddress'] = request.META['HTTP_X_FORWARDED_FOR']

    data = urllib.parse.urlencode({
        'firstname': user.first_name,
        'lastname': user.last_name,
        'email': user.email,
        'company': user.userprofile.organization,
        'hs_context': json.dumps(hs_context)
    })

    headers = {
        'Content-Type': 'application/x-www-form-urlencoded'
    }
    response = requests.post(settings.HUBSPOT_URL, data=data, headers=headers)

    if response.status_code != 204:
        logger.error("ERROR CODE %s. Could not save newly registered user to HubSpot:" +
                     "%s", response.status_code, data)
    return


class RegistrationView(BaseRegistrationView):
    """Extends default Django-registration HMAC view."""

    form_class = UserForm

    def register(self, form):
        new_user = super(RegistrationView, self).register(form)
        # create profile for new user and save in Django
        new_profile = UserProfile.create(user=new_user)
        new_profile.organization = form.cleaned_data.get('organization')
        new_user.userprofile = new_profile
        new_profile.save()
        new_user.save()

        _post_hubspot_lead(self.request, new_user)

        return new_user


class AppHomeView(LoginRequiredMixin, View):
    permission_classes = (IsAuthenticated, )
    authentication_classes = (TokenAuthentication, )

    def get(self, request, *args, **kwargs):
        template = 'app_home.html'
        return render(request, template)


class APIHomeView(LoginRequiredMixin, View):
    permission_classes = (IsAuthenticated, )
    authentication_classes = (TokenAuthentication, )

    def new_token(self, request):
        """Generate new auth token from within the profile page."""
        if request.method not in SAFE_METHODS:
            user = request.user
            if user.auth_token:
                user.auth_token.delete()
            user.auth_token = Token.objects.create(user=user)
            user.auth_token.save()
        return HttpResponseRedirect('{}'.format(reverse('api_home')))

    def get(self, request, *args, **kwargs):
        template = 'api_home.html'
        return render(request, template)


class UserProfileView(LoginRequiredMixin, View):
    permission_classes = (IsAuthenticated, )
    authentication_classes = (TokenAuthentication, )

    def get_initial(self, request):
        user = request.user
        self.initial = {
            'first_name': user.first_name,
            'last_name': user.last_name,
            'organization': user.userprofile.organization
        }
        return self.initial

    def get(self, request, *args, **kwargs):
        self.get_initial(request)
        form = UserProfileForm(initial=self.initial)
        template = 'registration/userprofile_update.html'
        return render(request, template, {'form': form})

    def post(self, request, *args, **kwargs):
        self.get_initial(request)
        user = request.user
        self.form = UserProfileForm(request._post, initial=self.initial)
        if self.form.is_valid():
            # Save changes to user, token, userprofile models
            user.first_name = self.form.cleaned_data.get('first_name')
            user.last_name = self.form.cleaned_data.get('last_name')
            user.userprofile.organization = self.form.cleaned_data.get('organization')
            user.save()
            user.userprofile.save()

        return HttpResponseRedirect('{}'.format(reverse('edit_profile')))


class ClimateAPIObtainAuthToken(ObtainAuthToken):
    """Anonymous endpoint for users to request tokens from for authentication."""

    throttle_classes = (ObtainAuthTokenThrottle,)
    serializer_class = AuthTokenSerializer


class ClimateAPIRefreshAuthToken(ClimateAPIObtainAuthToken):
    """Anonymous endpoint for users to refresh and request tokens from for authentication."""

    def post(self, request, *args, **kwargs):
        serializer = self.serializer_class(data=request.data,
                                           context={'request': request})
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data['user']
        if user.auth_token:
            user.auth_token.delete()
        user.auth_token = Token.objects.create(user=user)
        return Response({'token': user.auth_token.key})


class ClimateAPIObtainAuthTokenForCurrentUser(View):
    """Endpoint to allow session-authenticated Lab users to request their API token."""

    authentication_classes = (SessionAuthentication,)
    permission_classes = (IsAuthenticated,)
    serializer_class = AuthTokenSerializer

    def _set_cors_headers(self, request, response):
        # We need to handle CORS headers manually for this endpoint, as this is
        # the only endpoint in the API we want to allow credentials on, and we
        # only want it available to the Lab in production
        if settings.ENVIRONMENT in {'Development', 'Staging'}:
            response[ACCESS_CONTROL_ALLOW_ORIGIN] = request.META.get('HTTP_ORIGIN')
            patch_vary_headers(response, ['Origin'])
        else:
            response[ACCESS_CONTROL_ALLOW_ORIGIN] = settings.LAB_URL

        response[ACCESS_CONTROL_ALLOW_CREDENTIALS] = 'true'
        response[ACCESS_CONTROL_EXPOSE_HEADERS] = ', '.join(default_cors_headers)

    def options(self, request, *args, **kwargs):
        response = HttpResponse()
        self._set_cors_headers(request, response)
        response[ACCESS_CONTROL_ALLOW_HEADERS] = ', '.join(default_cors_headers)

        return response

    def get(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            token, created = Token.objects.get_or_create(user=request.user)
            response = JsonResponse({'token': token.key, 'email': request.user.email})
        else:
            response = HttpResponse(status=401)

        self._set_cors_headers(request, response)

        return response
