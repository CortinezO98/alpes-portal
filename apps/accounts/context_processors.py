from django.conf import settings


def social_auth(request):
    return {
        "facebook_auth_enabled": settings.FACEBOOK_AUTH_ENABLED,
        "google_auth_enabled": settings.GOOGLE_AUTH_ENABLED,
        "social_auth_enabled": (
            settings.FACEBOOK_AUTH_ENABLED or settings.GOOGLE_AUTH_ENABLED
        ),
    }
