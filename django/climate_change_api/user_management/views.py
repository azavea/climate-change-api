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



class RegistrationView(BaseRegistrationView):
    """ Extends default Django-registration HMAC view """
    form_class = UserForm


def edit_profile(request):
    """ User profile view allows editing and viewing non-unique fields of logged in user """

    # Redirect to log-in page if not logged in
    if not request.user.is_authenticated():
        return HttpResponseRedirect('{}'.format(reverse('auth_login')))

    #create userprofile if none yet
    if not hasattr(request.user, 'userprofile'):
        newprofile = UserProfile.create(user=request.user)
        request.user.userprofile = newprofile
        newprofile.save()

    user = request.user
    form = UserProfileForm(request.POST or None, initial={'first_name': user.first_name,
            'last_name': user.last_name,
            'email': user.email,
            'organization': user.userprofile.organization
        })
    if request.method == 'POST':
        if form.is_valid():
            # Save changes to user and userprofile models
            user.email = form.cleaned_data.get('email')
            user.first_name = form.cleaned_data.get('first_name')
            user.last_name = form.cleaned_data.get('last_name')
            user.userprofile.organization = form.cleaned_data.get('organization')
            user.save()
            user.userprofile.save()
            return HttpResponseRedirect('{}'.format(reverse('edit_profile')))

    context = {
        "form": form
    }

    return render(request, "registration/userprofile_update.html", context)
