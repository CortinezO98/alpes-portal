from django.conf import settings


def social_auth(request):
    return {
        "facebook_auth_enabled": settings.FACEBOOK_AUTH_ENABLED,
    }
