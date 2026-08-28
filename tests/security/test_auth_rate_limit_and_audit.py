import pytest
from django.urls import reverse

from apps.accounts.models import User
from apps.audit.models import AuditEvent, AuthThrottle


@pytest.mark.django_db
def test_failed_login_is_audited(client):
    response = client.post(
        reverse("accounts:login"),
        {"username": "nobody@example.com", "password": "wrong-password"},
        REMOTE_ADDR="192.0.2.10",
    )

    assert response.status_code == 200
    event = AuditEvent.objects.get(action=AuditEvent.Action.LOGIN_FAILURE)
    assert event.actor is None
    assert event.ip_hash
    assert event.metadata == {"rate_limited": False}


@pytest.mark.django_db
def test_login_is_blocked_after_repeated_failures(client):
    login_url = reverse("accounts:login")
    payload = {"username": "target@example.com", "password": "wrong-password"}

    for _ in range(5):
        client.post(login_url, payload, REMOTE_ADDR="192.0.2.20")

    response = client.post(login_url, payload, REMOTE_ADDR="192.0.2.20")

    assert response.status_code == 200
    assert "Demasiados intentos" in response.content.decode("utf-8")
    assert AuthThrottle.objects.filter(scope="login_ip", blocked_until__isnull=False).exists()
    assert AuditEvent.objects.filter(
        action=AuditEvent.Action.LOGIN_FAILURE,
        metadata__rate_limited=True,
    ).exists()


@pytest.mark.django_db
def test_successful_login_clears_failed_attempts_and_is_audited(client):
    user = User.objects.create_user(
        email="secure@example.com",
        password="SecurePass123!",
        role=User.Role.USER,
    )
    login_url = reverse("accounts:login")

    client.post(
        login_url,
        {"username": user.email, "password": "wrong-password"},
        REMOTE_ADDR="192.0.2.30",
    )
    response = client.post(
        login_url,
        {"username": user.email, "password": "SecurePass123!"},
        REMOTE_ADDR="192.0.2.30",
    )

    assert response.status_code == 302
    assert not AuthThrottle.objects.filter(scope__startswith="login_").exists()
    assert AuditEvent.objects.filter(
        action=AuditEvent.Action.LOGIN_SUCCESS,
        actor=user,
    ).exists()


@pytest.mark.django_db
def test_password_reset_requests_are_rate_limited_without_account_disclosure(client):
    reset_url = reverse("accounts:password-reset")
    done_url = reverse("accounts:password-reset-done")
    payload = {"email": "unknown@example.com"}

    for _ in range(5):
        response = client.post(reset_url, payload, REMOTE_ADDR="192.0.2.40")
        assert response.status_code == 302
        assert response.url == done_url

    response = client.post(reset_url, payload, REMOTE_ADDR="192.0.2.40")

    assert response.status_code == 302
    assert response.url == done_url
    assert AuthThrottle.objects.filter(
        scope="password_reset_ip",
        blocked_until__isnull=False,
    ).exists()
    assert AuditEvent.objects.filter(
        action=AuditEvent.Action.PASSWORD_RESET_REQUEST,
        metadata__rate_limited=True,
    ).exists()


@pytest.mark.django_db
def test_superadmin_user_creation_is_audited(client):
    superadmin = User.objects.create_superuser(
        email="root@example.com",
        password="SecurePass123!",
    )
    client.force_login(superadmin)

    response = client.post(
        reverse("accounts:user-management-create"),
        {
            "email": "new-user@example.com",
            "role": User.Role.USER,
            "password1": "StrongTemporaryPass123!",
            "password2": "StrongTemporaryPass123!",
        },
        REMOTE_ADDR="192.0.2.50",
    )

    assert response.status_code == 302
    created = User.objects.get(email="new-user@example.com")
    event = AuditEvent.objects.get(action=AuditEvent.Action.USER_CREATED)
    assert event.actor == superadmin
    assert event.target_id == str(created.pk)
    assert event.metadata["role"] == User.Role.USER
