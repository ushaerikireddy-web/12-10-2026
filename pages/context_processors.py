from django.conf import settings


def platform_context(request):
    return {
        'PLATFORM_NAME': getattr(settings, 'PLATFORM_NAME', 'VIDYA'),
        'PLATFORM_TAGLINE': getattr(settings, 'PLATFORM_TAGLINE', 'Where Knowledge Becomes Power.'),
    }
