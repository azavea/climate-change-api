"""
URLconf for registration and activation, using django-registration's
HMAC activation workflow.

"""

from django.conf.urls import include, url
from user_management.views import RegistrationView


urlpatterns = [
    url(r'^register/$',
        RegistrationView.as_view(),
        name='registration_register'),
    url(r'', include('registration.auth_urls')),
]
