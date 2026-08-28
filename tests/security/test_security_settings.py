from django.conf import settings


def test_shared_security_settings_are_enabled():
    assert settings.PASSWORD_RESET_TIMEOUT == 3600
    assert settings.SESSION_COOKIE_HTTPONLY is True
    assert settings.SESSION_COOKIE_SAMESITE == "Lax"
    assert settings.CSRF_COOKIE_SAMESITE == "Lax"
    assert settings.X_FRAME_OPTIONS == "DENY"
    assert settings.SECURE_CONTENT_TYPE_NOSNIFF is True


def test_production_security_settings(monkeypatch):
    monkeypatch.setenv("DJANGO_SECRET_KEY", "x" * 64)
    monkeypatch.setenv("DJANGO_ALLOWED_HOSTS", "example.com")
    monkeypatch.setenv("DJANGO_CSRF_TRUSTED_ORIGINS", "https://example.com")

    from config.settings import production

    assert production.DEBUG is False
    assert production.SECURE_SSL_REDIRECT is True
    assert production.SESSION_COOKIE_SECURE is True
    assert production.SESSION_COOKIE_HTTPONLY is True
    assert production.CSRF_COOKIE_SECURE is True
    assert production.SECURE_HSTS_SECONDS == 31536000
    assert production.SECURE_HSTS_INCLUDE_SUBDOMAINS is True
    assert production.SECURE_HSTS_PRELOAD is True
    assert production.X_FRAME_OPTIONS == "DENY"
