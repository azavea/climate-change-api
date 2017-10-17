from django.conf import settings


def links(request):
    return {
        'API_DOCUMENTATION_URL': settings.API_DOCUMENTATION_URL,
        'DEFAULT_TO_EMAIL': settings.DEFAULT_TO_EMAIL,
        'LAB_URN': settings.LAB_URN
    }
