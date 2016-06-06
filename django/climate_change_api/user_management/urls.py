"""
URLconf for registration and activation, using django-registration's
HMAC activation workflow.

"""

from django.conf.urls import include, url
from user_management import views
from django.contrib.auth import views as auth_views

urlpatterns = [
    url(r'^register/$',
        views.RegistrationView.as_view(),
        name='registration_register'),
    url(r'^profile/$', views.UserProfileView.as_view(), name='edit_profile'),
    url(r'^new_token/$', views.new_token, name='new_token'),
    url(r'', include('registration.auth_urls')),
]
