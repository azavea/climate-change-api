from django.conf import settings


def links(request):
    return {
        'API_DOCUMENTATION_URL': settings.API_DOCUMENTATION_URL,
    }
