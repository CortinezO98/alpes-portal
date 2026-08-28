import pytest
from allauth.account.models import EmailAddress
from django.core import mail
from django.test import override_settings
from django.urls import reverse

from apps.accounts.models import User
from apps.audit.models import AuditEvent


@pytest.mark.django_db
def test_public_signup_page_is_available(client):
    response = client.get(reverse("accounts:signup"))

    assert response.status_code == 200
    assert b"Crear cuenta" in response.content


@pytest.mark.django_db
def test_public_signup_creates_only_user_role_and_requires_verification(client):
    response = client.post(
        reverse("accounts:signup"),
        {
            "email": "public@example.com",
            "password1": "StrongPass123!",
            "password2": "StrongPass123!",
            "role": User.Role.SUPERADMIN,
            "is_staff": "on",
            "is_superuser": "on",
        },
    )

    assert response.status_code == 302
    user = User.objects.get(email="public@example.com")
    assert user.role == User.Role.USER
    assert user.is_staff is False
    assert user.is_superuser is False
    assert user.email_verification_required is True
    assert user.is_email_verified is False

    email_address = EmailAddress.objects.get(user=user, email=user.email)
    assert email_address.verified is False


@pytest.mark.django_db
def test_public_signup_is_audited(client):
    client.post(
        reverse("accounts:signup"),
        {
            "email": "audit-signup@example.com",
            "password1": "StrongPass123!",
            "password2": "StrongPass123!",
        },
    )

    user = User.objects.get(email="audit-signup@example.com")
    event = AuditEvent.objects.filter(
        action=AuditEvent.Action.USER_CREATED,
        target_id=str(user.pk),
    ).latest("created_at")

    assert event.metadata["source"] == "public_signup"
    assert event.metadata["role"] == User.Role.USER


@pytest.mark.django_db
def test_unverified_public_user_cannot_use_primary_login(client):
    user = User.objects.create_user(
        email="pending@example.com",
        password="StrongPass123!",
        role=User.Role.USER,
        email_verification_required=True,
        is_email_verified=False,
    )

    response = client.post(
        reverse("accounts:login"),
        {"username": user.email, "password": "StrongPass123!"},
    )

    assert response.status_code == 200
    assert b"Confirma tu correo" in response.content
    assert "_auth_user_id" not in client.session


@pytest.mark.django_db
def test_verified_public_user_can_use_primary_login(client):
    user = User.objects.create_user(
        email="verified@example.com",
        password="StrongPass123!",
        role=User.Role.USER,
        email_verification_required=True,
        is_email_verified=True,
    )

    response = client.post(
        reverse("accounts:login"),
        {"username": user.email, "password": "StrongPass123!"},
    )

    assert response.status_code == 302
    assert response.url == reverse("accounts:dashboard")


@pytest.mark.django_db
def test_admin_created_account_keeps_existing_login_behavior(client):
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


@pytest.mark.django_db
@override_settings(FACEBOOK_AUTH_ENABLED=False, GOOGLE_AUTH_ENABLED=False)
def test_auth_pages_link_back_to_public_portfolio(client):
    public_url = reverse("portfolio:home")

    login_response = client.get(reverse("accounts:login"))
    signup_response = client.get(reverse("accounts:signup"))

    assert login_response.status_code == 200
    assert signup_response.status_code == 200
    assert f'href="{public_url}"'.encode() in login_response.content
    assert f'href="{public_url}"'.encode() in signup_response.content
    assert b"portafolio p\xc3\xbablico" in login_response.content.lower()
    assert b"portafolio p\xc3\xbablico" in signup_response.content.lower()


@pytest.mark.django_db
@override_settings(EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend")
def test_public_signup_sends_branded_verification_email(client):
    client.post(
        reverse("accounts:signup"),
        {
            "email": "mail-check@example.com",
            "password1": "StrongPass123!",
            "password2": "StrongPass123!",
        },
    )

    assert len(mail.outbox) == 1
    message = mail.outbox[0]
    assert message.to == ["mail-check@example.com"]
    assert "Confirma tu correo" in message.subject
    assert "ALPES" in message.body
    assert "/cuenta/auth/confirm-email/" in message.body
