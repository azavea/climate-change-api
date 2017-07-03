"""URLconf for registration and activation, using django-registration's HMAC activation workflow."""

from django.conf.urls import include, url
from user_management.views import RegistrationView, UserProfileView
from django.conf import settings


urlpatterns = [
    url(r'^register/$',
        RegistrationView.as_view(),
        name='registration_register'),
    url(r'^profile/new_token/', UserProfileView().new_token, name='new_token'),
    url(r'^profile/$', UserProfileView.as_view(), name='edit_profile'),
    url(r'', include('registration.backends.hmac.urls')),
]

if settings.DEBUG:
    import debug_toolbar
    urlpatterns += [url(r'^__debug__/', include(debug_toolbar.urls))]
