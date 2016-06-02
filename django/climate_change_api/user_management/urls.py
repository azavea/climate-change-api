"""
URLconf for registration and activation, using django-registration's
HMAC activation workflow.

"""

from django.conf.urls import include, url
from user_management import views


urlpatterns = [
    url(r'^register/$',
        views.RegistrationView.as_view(),
        name='registration_register'),
    url(r'^profile/$', views.edit_profile, name='edit_profile'),
    url(r'', include('registration.auth_urls')),
]
