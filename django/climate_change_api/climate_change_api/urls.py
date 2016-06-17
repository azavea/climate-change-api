"""climate_change_api URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/1.9/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  url(r'^$', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  url(r'^$', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.conf.urls import url, include
    2. Add a URL to urlpatterns:  url(r'^blog/', include('blog.urls'))
"""
from django.conf import settings
from django.conf.urls import url, include
from django.contrib import admin
from django.contrib.staticfiles.urls import staticfiles_urlpatterns
from django.views.generic import RedirectView

from rest_framework import routers

from climate_data import views as climate_data_views


router = routers.DefaultRouter()
router.register(r'city', climate_data_views.CityViewSet)
router.register(r'climate-model', climate_data_views.ClimateModelViewSet)
router.register(r'scenario', climate_data_views.ScenarioViewSet)

urlpatterns = [
    url(r'^accounts/', include('user_management.urls')),
    url(r'^accounts/', include('registration.backends.hmac.urls')),
    url(r'^accounts/.*$', RedirectView.as_view(url='/accounts/login/')),
    url(r'^api/', include(router.urls)),
    url(r'^api/climate-data/(?P<city>[0-9]+)/(?P<scenario>.+)/$',
        climate_data_views.ClimateDataList.as_view(), name='climatedata-list'),
    url(r'^api-auth/', include('rest_framework.urls', namespace='rest_framework')),
    url(r'^admin/', admin.site.urls),

    # 3rd party
    url(r'^docs/', include('rest_framework_swagger.urls')),
    url(r'^healthcheck/', include('watchman.urls'))
]

if settings.DEBUG:
    urlpatterns += staticfiles_urlpatterns()
