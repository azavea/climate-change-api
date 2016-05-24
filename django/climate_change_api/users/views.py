from django.shortcuts import render, redirect
from django.http import HttpResponseRedirect

from rest_framework import viewsets, status

from users.models import APIUser
from users.serializers import APIUserSerializer
from users.forms import NewUserForm


def new_signup(request):
    if request.method == 'POST':
        form = NewUserForm(request.POST)
        if form.is_valid():
            form.save()
            # Temporarily set to /admin because the app is currently barebones
            return HttpResponseRedirect('/admin/')
    else:
        form = NewUserForm()
    return render(request, 'sign_up.html', {'form': form})


class APIUserViewSet(viewsets.ModelViewSet):
    """ Viewset for Django API """
    queryset = APIUser.objects.all()
    serializer_class = APIUserSerializer
    filter_fields = ('id', 'username', 'first_name', 'last_name', 'email', 'is_staff',
        'is_superuser', 'organization',)
    ordering_fields = ('id',)
