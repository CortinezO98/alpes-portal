import pytest
from django.urls import reverse

from apps.accounts.models import User


@pytest.mark.django_db
def test_user_cannot_access_admin_dashboard(client):
    user = User.objects.create_user(
        email="user@example.com",
        password="SecurePass123!",
        role=User.Role.USER,
    )

    client.force_login(user)

    response = client.get(
        reverse("accounts:admin-dashboard")
    )

    assert response.status_code == 403


@pytest.mark.django_db
def test_user_cannot_access_superadmin_dashboard(client):
    user = User.objects.create_user(
        email="user@example.com",
        password="SecurePass123!",
        role=User.Role.USER,
    )

    client.force_login(user)

    response = client.get(
        reverse("accounts:superadmin-dashboard")
    )

    assert response.status_code == 403


@pytest.mark.django_db
def test_admin_can_access_admin_dashboard(client):
    admin = User.objects.create_user(
        email="admin@example.com",
        password="SecurePass123!",
        role=User.Role.ADMIN,
    )

    client.force_login(admin)

    response = client.get(
        reverse("accounts:admin-dashboard")
    )

    assert response.status_code == 200


@pytest.mark.django_db
def test_admin_cannot_access_superadmin_dashboard(client):
    admin = User.objects.create_user(
        email="admin@example.com",
        password="SecurePass123!",
        role=User.Role.ADMIN,
    )

    client.force_login(admin)

    response = client.get(
        reverse("accounts:superadmin-dashboard")
    )

    assert response.status_code == 403


@pytest.mark.django_db
def test_superadmin_can_access_all_dashboards(client):
    superadmin = User.objects.create_superuser(
        email="superadmin@example.com",
        password="SecurePass123!",
    )

    client.force_login(superadmin)

    urls = [
        reverse("accounts:superadmin-dashboard"),
        reverse("accounts:admin-dashboard"),
        reverse("accounts:user-dashboard"),
    ]

    for url in urls:
        response = client.get(url)
        assert response.status_code == 200