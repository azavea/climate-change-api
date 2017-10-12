"""climate_change_api URL Configuration.

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

from rest_framework import routers

from climate_data import views as climate_data_views
from user_projects import views as user_projects_views
from user_management.views import (ClimateAPIObtainAuthToken, ClimateAPIRefreshAuthToken,
                                   AppHomeView)

if settings.DEBUG and settings.STATIC_URL_PATH:
    from django.contrib.staticfiles.urls import staticfiles_urlpatterns


router = routers.DefaultRouter()
router.include_root_view = False
router.register(r'city', climate_data_views.CityViewSet)
router.register(r'climate-model', climate_data_views.ClimateModelViewSet)
router.register(r'dataset', climate_data_views.ClimateDatasetViewSet)
router.register(r'scenario', climate_data_views.ScenarioViewSet)
router.register(r'project', user_projects_views.ProjectViewSet, base_name='project')

urlpatterns = [
    url(r'^$', AppHomeView.as_view(), name='app_home'),
    url(r'^accounts/', include('user_management.urls')),
    url(r'^api/', include(router.urls)),
    url(r'^api/city/(?P<city>[0-9]+)/map-cell/$',
        climate_data_views.CityMapCellListView.as_view(), name='city-map-cell-list'),
    url(r'^api/city/(?P<city>[0-9]+)/map-cell/(?P<dataset>.+)/$',
        climate_data_views.CityMapCellDatasetDetailView.as_view(),
        name='city-map-cell-dataset-detail'),
    url(r'^api/indicator/$',
        climate_data_views.IndicatorListView.as_view(), name='climateindicator-list'),
    url(r'^api/indicator/(?P<indicator>.+)/$',
        climate_data_views.IndicatorDetailView.as_view(), name='climateindicator-detail'),
    url(r'^api/climate-data/(?P<city>[0-9]+)/(?P<scenario>.+)/indicator/(?P<indicator>.+)/$',
        climate_data_views.IndicatorDataView.as_view(), name='climateindicator-get'),
    url(r'^api/climate-data/(?P<city>[0-9]+)/(?P<scenario>.+)/$',
        climate_data_views.ClimateDataView.as_view(), name='climatedata-list'),
    url(r'^api/historic-range/$',
        climate_data_views.HistoricDateRangeView.as_view({'get': 'list'}), name='historic-list'),
    url(r'^api/region/$',
        climate_data_views.RegionListView.as_view(), name='region-list'),
    url(r'^api/region/(?P<region>[0-9]+)/$',
        climate_data_views.RegionDetailView.as_view(), name='region-detail'),
    url(r'^api/region/(?P<region>[0-9]+)\.(?P<format>[json|pbf|api]+)/?$',
        climate_data_views.RegionDetailView.as_view(), name='region-detail'),
    url(r'^api/datacheck/$', climate_data_views.DataCheckView.as_view(), name='data-check'),
    url(r'^api-auth/', include('rest_framework.urls', namespace='rest_framework')),
    url(r'^api-token-auth/', ClimateAPIObtainAuthToken.as_view()),
    url(r'^api-refresh-token-auth/', ClimateAPIRefreshAuthToken.as_view()),
    url(r'^admin/', admin.site.urls),

    # 3rd party
    url(r'^healthcheck/', include('watchman.urls'))
]

if settings.DEBUG and settings.STATIC_URL_PATH:
    urlpatterns += staticfiles_urlpatterns()

if settings.DEBUG:
    import debug_toolbar
    urlpatterns += [url(r'^__debug__/', include(debug_toolbar.urls))]
