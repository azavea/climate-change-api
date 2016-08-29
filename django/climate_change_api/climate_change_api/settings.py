"""
Django settings for climate_change_api project.

Generated by 'django-admin startproject' using Django 1.9.2.

For more information on this file, see
https://docs.djangoproject.com/en/1.9/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/1.9/ref/settings/
"""

import os
import requests
import boto3

import docker_helper

# Build paths inside the project like this: os.path.join(BASE_DIR, ...)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/1.9/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = os.getenv('CC_SECRET_KEY', 'SECRET_KEY_dm!*rrb%!r%$qmei!de@hyc0a_z0!hq(&$g63fs')

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True if os.getenv('CC_DEBUG', False) else False


if not DEBUG and SECRET_KEY.startswith('SECRET_KEY'):
    # prevent from running in production mode with default secret key
    raise Exception('Default SECRET_KEY in production mode')

if DEBUG:
    docker_helper.wait_for_database()

ALLOWED_HOSTS = os.getenv('CC_ALLOWED_HOSTS', '').split(',')

if '' in ALLOWED_HOSTS:
    ALLOWED_HOSTS.remove('')

# solution from https://dryan.com/articles/elb-django-allowed-hosts/
EC2_PRIVATE_IP = None
AWS_AVAILBILITY_ZONE = None

try:
    EC2_PRIVATE_IP = requests.get('http://169.254.169.254/latest/meta-data/local-ipv4',
                                  timeout=0.1).text
    AWS_AVAILABILITY_ZONE = requests.get('http://169.254.169.254/latest/meta-data/placement/availability-zone',  # NOQA
                                         timeout=0.1).text
except requests.exceptions.RequestException:
    pass

if EC2_PRIVATE_IP:
    ALLOWED_HOSTS.append(EC2_PRIVATE_IP)

# Application definition

INSTALLED_APPS = [

    # Priority apps: override defaults in django core
    'user_management',

    # Django core
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',

    # 3rd-party
    'storages',
    'django_filters',
    'rest_framework',
    'rest_framework_gis',
    'rest_framework.authtoken',
    'rest_framework_swagger',
    'bootstrap3',
    'watchman',

    # Apps
    'climate_data',
]

if DEBUG:
    INSTALLED_APPS += ['django_extensions']


# Email
# https://docs.djangoproject.com/en/1.9/topics/email/
if DEBUG:
    EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'
else:
    EMAIL_BACKEND = 'django_amazon_ses.backends.boto.EmailBackend'
DEFAULT_FROM_EMAIL = os.getenv('CC_FROM_EMAIL', 'support@futurefeelslike.com')


MIDDLEWARE_CLASSES = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.auth.middleware.SessionAuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'climate_change_api.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]


WSGI_APPLICATION = 'climate_change_api.wsgi.application'

AUTH_PROFILE_MODULE = 'user_management.UserProfile'


# Database
# https://docs.djangoproject.com/en/1.9/ref/settings/#databases

DATABASES = {
    'default': {
        'ENGINE': 'django.contrib.gis.db.backends.postgis',
        'NAME': os.getenv('CC_DB_DATABASE', 'climate'),
        'USER': os.getenv('CC_DB_USER', 'climate'),
        'PASSWORD': os.getenv('CC_DB_PASSWORD', 'climate'),
        'HOST': os.getenv('CC_DB_HOST', 'postgres')
    }
}


# Password validation
# https://docs.djangoproject.com/en/1.9/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]

# Django-Registration
# https://django-registration.readthedocs.io/en/2.1/
ACCOUNT_ACTIVATION_DAYS = 14


# Internationalization
# https://docs.djangoproject.com/en/1.9/topics/i18n/

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'UTC'

USE_I18N = True

USE_L10N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/1.9/howto/static-files/

if os.getenv('COMMIT'):
    STATICFILES_STORAGE = 'storages.backends.s3boto.S3BotoStorage'
    AWS_STORAGE_BUCKET_NAME = os.getenv('CC_S3STORAGE_BUCKET')
    AWS_LOCATION = '/{}/static'.format(os.getenv('COMMIT'))
    AWS_HEADERS = {
        'Cache-Control': 'max-age={}'.format(os.getenv('AWS_CACHE_DURATION')),
    }
else:
    STATIC_ROOT = '/media/static/'
    STATIC_URL = '/static/'

# Logging
# https://docs.djangoproject.com/en/1.9/topics/logging/
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler'
        }
    },
    'loggers': {
        'django': {
            'handlers': ['console'],
            'level': os.getenv('DJANGO_LOG_LEVEL', 'INFO')
        },
        'climate_data': {
            'handlers': ['console'],
            'level': os.getenv('DJANGO_LOG_LEVEL', 'INFO')
        }
    }
}


# Django Rest Framework
# http://www.django-rest-framework.org/
REST_FRAMEWORK = {
    'DEFAULT_FILTER_BACKENDS': [
        'rest_framework.filters.DjangoFilterBackend',
        'rest_framework.filters.OrderingFilter'
    ],
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.LimitOffsetPagination',
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticated'
        ],
    'DEFAULT_AUTHENTICATION_CLASSES': ('rest_framework.authentication.TokenAuthentication',
                                       'rest_framework.authentication.SessionAuthentication',),
    'DEFAULT_RENDERER_CLASSES': ('rest_framework.renderers.JSONRenderer',
                                 'rest_framework.renderers.BrowsableAPIRenderer',),
    'PAGE_SIZE': 20,
    'TEST_REQUEST_DEFAULT_FORMAT': 'json'
}


# Django REST Swagger
# https://django-rest-swagger.readthedocs.io/en/latest/
SWAGGER_SETTINGS = {
    'api_version': '0.1.0',
    'doc_expansion': 'list',
    'is_authenticated': True,
    'permission_denied_handler': 'climate_data.views.swagger_docs_permission_denied_handler'
}


# Watchman
# http://django-watchman.readthedocs.io/en/latest/
WATCHMAN_ERROR_CODE = 503
WATCHMAN_CHECKS = (
    'watchman.checks.caches',
    'watchman.checks.databases',
)

# Boto setup
if DEBUG:
    boto3.setup_default_session(profile_name='climate')

SQS_QUEUE_NAME = os.getenv('CC_SQS_QUEUE_NAME', 'climate-api')
SQS_IMPORT_QUEUE_ATTRIBUTES = {
    'VisibilityTimeout': str(3600*4),
    'ReceiveMessageWaitTimeSeconds': str(10),
    'MaximumMessageSize': str(1024)
}

if DEBUG:
    dev_user = os.getenv('DEV_USER') if os.getenv('DEV_USER') else 'developer'
    SQS_QUEUE_NAME = 'cc-api-{}'.format(dev_user)
    SQS_IMPORT_QUEUE_ATTRIBUTES = {
        'VisibilityTimeout': str(3600)
    }
