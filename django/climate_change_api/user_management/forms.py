from django import forms
from user_management.models import UserProfile, ClimateUser
from registration.forms import RegistrationFormUniqueEmail


class UserForm(RegistrationFormUniqueEmail):
    """Extends django-registration default user sign up form with other User model fields.

    Enforces 1 account per e-mail.
    """

    email = forms.EmailField(help_text=None, widget=forms.TextInput(attrs={'placeholder': ''}))
    first_name = forms.CharField(max_length=30, widget=forms.TextInput(attrs={'placeholder': ''}))
    last_name = forms.CharField(max_length=30, widget=forms.TextInput(attrs={'placeholder': ''}))
    organization = forms.CharField(max_length=255,
                                   widget=forms.TextInput(attrs={'placeholder': ''}))
    password1 = forms.CharField(help_text=None,
                                label='Password',
                                widget=forms.PasswordInput(attrs={'placeholder': ''}))
    password2 = forms.CharField(help_text=None,
                                label='Password confirmation',
                                widget=forms.PasswordInput(attrs={'placeholder': ''}))

    class Meta:
        model = ClimateUser
        fields = ('email', 'first_name', 'last_name', 'organization',)


class UserProfileForm(forms.ModelForm):
    """Defines mutable fields in the user profile and validates user-made data changes."""

    first_name = forms.CharField(max_length=30, required=True)
    last_name = forms.CharField(max_length=30, required=True)
    organization = forms.CharField(max_length=255, required=True)

    class Meta:
        model = UserProfile
        fields = ('first_name', 'last_name', 'organization',)
