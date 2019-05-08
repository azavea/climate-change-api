"""URLconf for registration and activation, using django-registration's HMAC activation workflow."""

from django.conf.urls import include, url
from user_management.views import RegistrationView, UserProfileView, APIHomeView


urlpatterns = [
    url(r'^register/$',
        RegistrationView.as_view(),
        name='django_registration_register'),
    url(r'^api/new_token/', APIHomeView().new_token, name='new_token'),
    url(r'^profile/$', UserProfileView.as_view(), name='edit_profile'),
    url(r'^api/$', APIHomeView.as_view(), name='api_home'),
    url(r'', include('django_registration.backends.activation.urls')),
    url(r'', include('django.contrib.auth.urls')),
]
