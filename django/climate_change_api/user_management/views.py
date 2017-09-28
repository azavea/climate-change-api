"""Customized version of Django-registration plug-in's HMAC implementation.

A two-step (registration followed by activation) workflow, implemented by emailing an HMAC-verified
timestamped activation token to the user on signup.
"""

import requests
import logging
from django.shortcuts import render
from django.conf import settings
from django.urls import reverse
from django.http import HttpResponseRedirect
from django.views.generic import View
from django.contrib.auth.mixins import LoginRequiredMixin

from registration.backends.hmac.views import RegistrationView as BaseRegistrationView
from rest_framework.authtoken.models import Token
from rest_framework.authtoken.views import ObtainAuthToken
from rest_framework.authentication import TokenAuthentication
from rest_framework.permissions import IsAuthenticated, SAFE_METHODS

from user_management.forms import UserForm, UserProfileForm
from user_management.models import UserProfile
from user_management.throttling import ObtainAuthTokenThrottle
from user_management.serializers import AuthTokenSerializer


logger = logging.getLogger(__name__)


def _post_salesforce_lead(user):
    """Register new external users to Salesforce."""
    if user.email.endswith(settings.COMPANY_DOMAIN):
        return

    data = {
        'oid': settings.SALESFORCE_OID,
        'Campaign_ID': settings.SALESFORCE_CAMPAIGN_ID,
        settings.SALESFORCE_CONTACT_OUTREACH: '1',
        settings.SALESFORCE_VALIDATION: '1',  # Disable Validation
        'lead_source': 'Web',
        'first_name': user.first_name,
        'last_name': user.last_name,
        'email': user.email,
        'company': user.userprofile.organization,
    }

    response = requests.post(settings.SALESFORCE_URL, data=data)

    if response.status_code != 200:
        logger.error("ERROR CODE %s. Could not save newly registered user to Salesforce:" +
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

        # Also save user info to Salesforce
        _post_salesforce_lead(new_user)

        return new_user


class AppHomeView(LoginRequiredMixin, View):
    permission_classes = (IsAuthenticated, )
    authentication_classes = (TokenAuthentication, )

    def get(self, request, *args, **kwargs):
        context = {'lab_urn': settings.LAB_URN}
        template = 'app_home.html'
        return render(request, template, context)


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
