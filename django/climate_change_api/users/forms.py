from django import forms
from django.shortcuts import redirect
from django.contrib.auth.forms import UserCreationForm
from users.models import APIUser


class NewUserForm(UserCreationForm):

    class Meta:
        model = APIUser
        fields = ('first_name', 'last_name', 'email', 'organization', 'username',)
