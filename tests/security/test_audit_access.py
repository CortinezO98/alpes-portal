import pytest
from django.urls import reverse

from apps.accounts.models import User
from apps.audit.models import AuditEvent


@pytest.mark.django_db
def test_audit_requires_authentication(client):
    response = client.get(reverse("audit:event-list"))

    assert response.status_code == 302
    assert reverse("accounts:login") in response.url


@pytest.mark.django_db
def test_regular_user_cannot_view_audit(client):
    user = User.objects.create_user(
        email="member@example.com",
        password="SecurePass123!",
        role=User.Role.USER,
    )
    client.force_login(user)

    response = client.get(reverse("audit:event-list"))

    assert response.status_code == 403


@pytest.mark.django_db
def test_admin_cannot_view_audit(client):
    user = User.objects.create_user(
        email="admin@example.com",
        password="SecurePass123!",
        role=User.Role.ADMIN,
    )
    client.force_login(user)

    response = client.get(reverse("audit:event-list"))

    assert response.status_code == 403


@pytest.mark.django_db
def test_superadmin_can_view_audit_and_filter_events(client):
    user = User.objects.create_superuser(
        email="owner@example.com",
        password="SecurePass123!",
    )
    AuditEvent.objects.create(actor=user, action=AuditEvent.Action.USER_CREATED)
    AuditEvent.objects.create(actor=user, action=AuditEvent.Action.LOGIN_SUCCESS)
    client.force_login(user)

    response = client.get(
        reverse("audit:event-list"),
        {"action": AuditEvent.Action.USER_CREATED},
    )

    assert response.status_code == 200
    assert list(response.context["events"])[0].action == AuditEvent.Action.USER_CREATED
    assert len(response.context["events"]) == 1
