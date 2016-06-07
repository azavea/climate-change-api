"""
Customized of Django-registration plug-in's HMAC implementation
A two-step (registration followed by activation) workflow, implemented
by emailing an HMAC-verified timestamped activation token to the user
on signup.

"""

from registration.backends.hmac.views import RegistrationView as BaseRegistrationView
from user_management.forms import UserForm, UserProfileForm
from user_management.models import UserProfile
from django.shortcuts import render
from django.core.urlresolvers import reverse
from django.http import HttpResponseRedirect
from django.views.generic import View

from rest_framework.authtoken.models import Token
from rest_framework.authentication import TokenAuthentication
from rest_framework.permissions import IsAuthenticated, SAFE_METHODS


class RegistrationView(BaseRegistrationView):
    """ Extends default Django-registration HMAC view """
    form_class = UserForm


class UserProfileView(View):
    permission_classes = (IsAuthenticated, )
    authentication_classes = (TokenAuthentication, )

    def create_new_profile(self, request):
        # Create userprofile instance
        if not hasattr(request.user, 'userprofile'):
            newprofile = UserProfile.create(user=request.user)
            request.user.userprofile = newprofile
            newprofile.save()

    def get_initial(self, request):
        user = request.user
        self.initial = {
            'first_name': user.first_name,
            'last_name': user.last_name,
            'email': user.email,
            'organization': user.userprofile.organization
        }
        return self.initial

    def get(self, request, *args, **kwargs):
        #If first time signing in, create user profile
        self.create_new_profile(request)

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
            user.email = self.form.cleaned_data.get('email')
            user.first_name = self.form.cleaned_data.get('first_name')
            user.last_name = self.form.cleaned_data.get('last_name')
            user.userprofile.organization = self.form.cleaned_data.get('organization')
            user.save()
            user.userprofile.save()

        return HttpResponseRedirect('{}'.format(reverse('edit_profile')))

    def new_token(self, request):
        """ Generate new auth token"""
        if request.method not in SAFE_METHODS:
            user = request.user
            if user.auth_token:
                user.auth_token.delete()
            user.auth_token = Token.objects.create(user=user)
            user.auth_token.save()
        return HttpResponseRedirect('{}'.format(reverse('edit_profile')))
