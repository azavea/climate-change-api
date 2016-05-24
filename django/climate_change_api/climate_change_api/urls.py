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

from rest_framework import routers

from climate_data import views as climate_data_views
from users import views as users_views
from users.forms import NewUserForm


router = routers.DefaultRouter()
router.register(r'users', users_views.APIUserViewSet)
router.register(r'city', climate_data_views.CityViewSet)
router.register(r'climate-data', climate_data_views.ClimateDataViewSet)
router.register(r'climate-model', climate_data_views.ClimateModelViewSet)


urlpatterns = [
    url(r'^admin/', admin.site.urls),
    url(r'^api/', include(router.urls)),
    url(r'^api-auth/', include('rest_framework.urls', namespace='rest_framework')),
    url(r'^register/', users_views.new_signup, name='new_signup'),
]

if settings.DEBUG:
    urlpatterns += staticfiles_urlpatterns()
