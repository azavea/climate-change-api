from django import forms
from django.contrib.auth.models import User
from registration.forms import RegistrationFormUniqueEmail


class NewUserForm(RegistrationFormUniqueEmail):
    """ Extend django-registration default user sign up form with other User model fields
        Enforces 1 account per e-mail
    """

    email = forms.CharField(help_text=None)

    class Meta:
        model = User
        fields = ('username', 'first_name', 'last_name', 'email',)
