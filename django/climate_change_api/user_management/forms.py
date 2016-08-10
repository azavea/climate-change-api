from django import forms
from django.contrib.auth.models import User
from user_management.models import UserProfile
from registration.forms import RegistrationFormUniqueEmail


class UserForm(RegistrationFormUniqueEmail):
    """ Extend django-registration default user sign up form with other User model fields
        Enforces 1 account per e-mail
    """

    email = forms.EmailField(help_text=None)
    first_name = forms.CharField(max_length=30)
    last_name = forms.CharField(max_length=30)

    class Meta:
        model = User
        fields = ('username', 'first_name', 'last_name', 'email',)


class UserProfileForm(forms.ModelForm):
    """ Defines mutable fields in the user profile and validates user-made data changes
    """

    email = forms.EmailField(help_text=None, required=True)
    first_name = forms.CharField(max_length=30, required=False)
    last_name = forms.CharField(max_length=30, required=False)
    organization = forms.CharField(required=False)

    class Meta:
        model = UserProfile
        fields = ('first_name', 'last_name', 'email', 'organization',)

    def clean_email(self):
        """Ensures unique emails"""
        username = self.cleaned_data.get('username')
        old_email = self.initial.get('email')
        new_email = self.cleaned_data.get('email')
        if old_email == new_email:
            return old_email
        elif new_email and User.objects.filter(email=new_email).exclude(username=username).count():
            raise forms.ValidationError('This email address is already in use. Please supply a different email address.')
        return new_email
