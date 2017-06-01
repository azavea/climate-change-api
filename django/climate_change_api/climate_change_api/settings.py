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

from . import docker_helper

# Build paths inside the project like this: os.path.join(BASE_DIR, ...)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/1.9/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = os.getenv('CC_SECRET_KEY', 'SECRET_KEY_dm!*rrb%!r%$qmei!de@hyc0a_z0!hq(&$g63fs')

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = os.getenv('CC_DEBUG', False)
if DEBUG == 'False' or DEBUG == 'false':
    DEBUG = False


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
    AWS_AVAILABILITY_ZONE = requests.get('http://169.254.169.254/latest/meta-data/placement/availability-zone',  # NOQA: E501
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
    'rest_framework_extensions',
    'rest_framework_gis',
    'rest_framework.authtoken',
    'corsheaders',
    'bootstrap3',
    'watchman',
    'postgres_stats',
    'static_precompiler',

    # Apps
    'climate_data',
    'user_projects',
]

if DEBUG:
    INSTALLED_APPS += ['django_extensions']


# allow read-only CORS requests
CORS_ORIGIN_ALLOW_ALL = True
CORS_ALLOW_METHODS = ('GET', 'PUT', 'PATCH', 'DELETE', 'POST', 'OPTIONS')
CORS_REPLACE_HTTPS_REFERER = True


# Email
# https://docs.djangoproject.com/en/1.9/topics/email/
if DEBUG:
    EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'
else:
    EMAIL_BACKEND = 'django_amazon_ses.backends.boto.EmailBackend'
DEFAULT_FROM_EMAIL = os.getenv('CC_FROM_EMAIL', 'noreply@climate.azavea.com')
COMPANY_DOMAIN = '@azavea.com'

MIDDLEWARE_CLASSES = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'corsheaders.middleware.CorsPostCsrfMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.auth.middleware.SessionAuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'rollbar.contrib.django.middleware.RollbarNotifierMiddleware'
]

if not DEBUG:
    ROLLBAR = {
        'access_token': os.getenv('CC_ROLLBAR_SERVER_SIDE_ACCESS_TOKEN'),
        'environment': os.getenv('CC_STACK_TYPE'),
        'root': os.getcwd()
    }

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
                'user_management.context_processors.links',
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


# Cache
# https://docs.djangoproject.com/en/1.9/ref/settings/#caches

CACHE_LOCATION = os.getenv('CC_CACHE_HOST', 'memcached') + ':' + os.getenv('CC_CACHE_PORT', '11211')
if DEBUG:
    CACHE_BACKEND = 'django.core.cache.backends.memcached.PyLibMCCache'
else:
    CACHE_BACKEND = 'django_elasticache.memcached.ElastiCache'

CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
    },
    'api_views': {
        'BACKEND': CACHE_BACKEND,
        'LOCATION': CACHE_LOCATION,
    },
    # Separation of concerns for throttling cache
    'api_throttling': {
        'BACKEND': CACHE_BACKEND,
        'LOCATION': CACHE_LOCATION
    },
    'bypass': {
        'BACKEND': 'django.core.cache.backends.dummy.DummyCache',
    }
}

API_VIEW_DEFAULT_CACHE_TIMEOUT = 60 * 60 * 24


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
REGISTRATION_OPEN = True


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
    STATIC_PRECOMPILER_ROOT = '/media/static'
    STATIC_PRECOMPILER_FINDER_LIST_FILES = True
    STATIC_URL_PATH = False
else:

    STATIC_ROOT = '/media/static/'
    STATIC_URL = '/static/'
    STATIC_URL_PATH = True

STATICFILES_FINDERS = (
    'django.contrib.staticfiles.finders.FileSystemFinder',
    'django.contrib.staticfiles.finders.AppDirectoriesFinder',
    'static_precompiler.finders.StaticPrecompilerFinder',
)


# SCSS Static Compiler
# http://django-static-precompiler.readthedocs.io/en/stable/#libsass
STATIC_PRECOMPILER_COMPILERS = (
    ('static_precompiler.compilers.libsass.SCSS', {
        "precision": 8,
        "load_paths": ["/opt/django/scss/global"]
    }),
)


# Logging
# https://docs.djangoproject.com/en/1.9/topics/logging/
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'import_failures': {
            'class': 'logging.Formatter',
            'format': 'IMPORT_FAILURE %(asctime)s %(message)s',
        }
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
        },
        'console_import_failures': {
            'class': 'logging.StreamHandler',
            'formatter': 'import_failures',
        },
        'log_file_import_failures': {
            'class': 'logging.FileHandler',
            'filename': '/var/log/import_error.log',
            'formatter': 'import_failures',
        },
    },
    'loggers': {
        'django': {
            'handlers': ['console'],
            'level': os.getenv('DJANGO_LOG_LEVEL', 'INFO')
        },
        'climate_data': {
            'handlers': ['console'],
            'level': os.getenv('DJANGO_LOG_LEVEL', 'INFO')
        },
        'climate_data_import_failures': {
            'handlers': ['log_file_import_failures', 'console_import_failures'],
            'level': 'DEBUG',
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
    'DEFAULT_AUTHENTICATION_CLASSES': ['rest_framework.authentication.TokenAuthentication'],
    'DEFAULT_RENDERER_CLASSES': ['rest_framework.renderers.JSONRenderer'],
    'PAGE_SIZE': 20,
    'TEST_REQUEST_DEFAULT_FORMAT': 'json',
    'DEFAULT_THROTTLE_RATES': {
        'sustained': '5000/day',
        'burst': '20/min',
    },
}

# only enable browsable API in development
if DEBUG:
    REST_FRAMEWORK['DEFAULT_AUTHENTICATION_CLASSES'].append('rest_framework.authentication.SessionAuthentication')  # NOQA: E501
    REST_FRAMEWORK['DEFAULT_RENDERER_CLASSES'].append('rest_framework.renderers.BrowsableAPIRenderer')  # NOQA: E501


# Django Rest Framework extensions
# http://chibisov.github.io/drf-extensions/docs/
REST_FRAMEWORK_EXTENSIONS = {
    'DEFAULT_CACHE_ERRORS': False,
    'DEFAULT_CACHE_RESPONSE_TIMEOUT': API_VIEW_DEFAULT_CACHE_TIMEOUT,
    'DEFAULT_USE_CACHE': 'api_views',
}


# Statsd
# http://statsd.readthedocs.io/en/v3.2.1/
STATSD_HOST = 'statsite'
STATSD_PORT = 8125
# TODO: Include environment in prefix
STATSD_PREFIX = 'climate'


# Watchman
# http://django-watchman.readthedocs.io/en/latest/
WATCHMAN_ERROR_CODE = 503
WATCHMAN_CHECKS = (
    'watchman.checks.caches',
    'watchman.checks.databases',
)


# Salesforce
SALESFORCE_URL = 'https://webto.salesforce.com/servlet/servlet.WebToLead?encoding=UTF-8'
SALESFORCE_OID = '00D30000000efK8'  # Azavea Salesforce ID
SALESFORCE_CAMPAIGN_ID = '701130000027aQw'  # Climate Beta Test campaign in Salesforce
SALESFORCE_CONTACT_OUTREACH = '00N1300000B4tSR'  # Contact Outreach 'Climate Beta Test'
SALESFORCE_VALIDATION = '00N30000004RyN1'  # Toggle lead validation


# Boto setup
if DEBUG:
    boto3.setup_default_session(profile_name='climate')

SQS_QUEUE_NAME = os.getenv('CC_SQS_QUEUE_NAME', 'climate-api')
SQS_IMPORT_QUEUE_ATTRIBUTES = {
    'VisibilityTimeout': str(3600 * 4),
    'ReceiveMessageWaitTimeSeconds': str(10),
    'MaximumMessageSize': str(1024)
}
SQS_MAX_RETRIES = 10

if DEBUG:
    dev_user = os.getenv('DEV_USER') if os.getenv('DEV_USER') else 'developer'
    SQS_QUEUE_NAME = 'cc-api-{}'.format(dev_user)
    SQS_IMPORT_QUEUE_ATTRIBUTES = {
        'VisibilityTimeout': str(3600)
    }


AUTH_USER_MODEL = 'user_management.ClimateUser'

API_DOCUMENTATION_URL = 'https://docs.climate.azavea.com/'

if DEBUG:
    API_DOCUMENTATION_URL = 'http://localhost:8084/'
