"""
A two-step (registration followed by activation) workflow, implemented
by emailing an HMAC-verified timestamped activation token to the user
on signup.

"""
from registration.backends.hmac.views import RegistrationView as BaseRegistrationView
from user_management.forms import NewUserForm


# Extends default Django-registration HMAC view
class RegistrationView(BaseRegistrationView):
    form_class = NewUserForm
