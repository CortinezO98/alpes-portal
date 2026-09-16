from types import SimpleNamespace

import pytest
from django.conf import settings
from django.test import override_settings
from django.urls import reverse

from apps.accounts.adapters import AlpesAccountAdapter, AlpesSocialAccountAdapter
from apps.accounts.models import User


@pytest.mark.django_db
def test_public_signup_is_closed(client):
    response = client.get(reverse("account_signup"))

    assert response.status_code == 200
    assert b"registro p\xc3\xbablico est\xc3\xa1 deshabilitado" in response.content.lower()
    assert b"administraci\xc3\xb3n" in response.content.lower()


def test_account_adapter_disables_public_signup():
    adapter = AlpesAccountAdapter()

    assert adapter.is_open_for_signup(request=None) is False


def test_social_adapter_disables_new_social_accounts():
    adapter = AlpesSocialAccountAdapter()

    assert adapter.is_open_for_signup(request=None, sociallogin=None) is False


@pytest.mark.django_db
def test_admin_created_account_can_use_primary_login(client):
    user = User.objects.create_user(
        email="managed@example.com",
        password="StrongPass123!",
        role=User.Role.USER,
        email_verification_required=False,
        is_email_verified=False,
    )

    response = client.post(
        reverse("accounts:login"),
        {"username": user.email, "password": "StrongPass123!"},
    )

    assert response.status_code == 302
    assert response.url == reverse("accounts:dashboard")


@pytest.mark.django_db
def test_login_explains_managed_access_and_has_no_signup_link(client):
    response = client.get(reverse("accounts:login"))
    content = response.content.decode("utf-8")

    assert response.status_code == 200
    assert "Las cuentas son habilitadas por la administración de ALPES." in content
    assert "Crear cuenta" not in content
    assert f'href="{reverse("portfolio:home")}"' in content


@pytest.mark.django_db
@override_settings(FACEBOOK_AUTH_ENABLED=False)
def test_facebook_button_is_hidden_without_credentials(client):
    response = client.get(reverse("accounts:login"))

    assert response.status_code == 200
    assert b"Continuar con Facebook" not in response.content
    assert b"Iniciar sesi\xc3\xb3n con correo" in response.content


@pytest.mark.django_db
@override_settings(GOOGLE_AUTH_ENABLED=False)
def test_google_button_is_hidden_without_credentials(client):
    response = client.get(reverse("accounts:login"))

    assert response.status_code == 200
    assert b"Continuar con Google" not in response.content
    assert b"Iniciar sesi\xc3\xb3n con correo" in response.content


def test_social_email_authentication_is_enabled_for_managed_providers():
    assert settings.SOCIALACCOUNT_PROVIDERS["google"]["EMAIL_AUTHENTICATION"] is True
    assert settings.SOCIALACCOUNT_PROVIDERS["facebook"]["EMAIL_AUTHENTICATION"] is True
    assert settings.SOCIALACCOUNT_EMAIL_AUTHENTICATION_AUTO_CONNECT is True


@pytest.mark.django_db
def test_facebook_email_is_trusted_only_for_existing_active_local_account():
    adapter = AlpesSocialAccountAdapter()
    provider = SimpleNamespace(id="facebook")

    assert adapter.is_email_verified(provider, "missing@example.com") is False

    user = User.objects.create_user(
        email="existing@example.com",
        password="StrongPass123!",
        role=User.Role.USER,
        is_active=True,
    )
    assert adapter.is_email_verified(provider, user.email) is True

    user.is_active = False
    user.save(update_fields=("is_active",))
    assert adapter.is_email_verified(provider, user.email) is False
