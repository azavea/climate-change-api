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
from user_projects import views as user_projects_views
from user_management.views import ClimateAPIObtainAuthToken


router = routers.DefaultRouter()
router.register(r'city', climate_data_views.CityViewSet)
router.register(r'climate-model', climate_data_views.ClimateModelViewSet)
router.register(r'scenario', climate_data_views.ScenarioViewSet)
router.register(r'project', user_projects_views.ProjectViewSet, base_name='project')

urlpatterns = [
    url(r'^$', RedirectView.as_view(pattern_name='edit_profile')),
    url(r'^accounts/', include('user_management.urls')),
    url(r'^api/', include(router.urls)),
    url(r'^api/indicator/$',
        climate_data_views.climate_indicator_list, name='climateindicator-list'),
    url(r'^api/climate-data/(?P<city>[0-9]+)/(?P<scenario>.+)/indicator/(?P<indicator>.+)/$',
        climate_data_views.climate_indicator, name='climateindicator-get'),
    url(r'^api/climate-data/(?P<city>[0-9]+)/(?P<scenario>.+)/$',
        climate_data_views.climate_data_list, name='climatedata-list'),
    url(r'^api-auth/', include('rest_framework.urls', namespace='rest_framework')),
    url(r'^api-token-auth/', ClimateAPIObtainAuthToken.as_view()),
    url(r'^admin/', admin.site.urls),

    # 3rd party
    url(r'^docs/', include('rest_framework_swagger.urls')),
    url(r'^healthcheck/', include('watchman.urls'))
]

if settings.DEBUG:
    urlpatterns += staticfiles_urlpatterns()
