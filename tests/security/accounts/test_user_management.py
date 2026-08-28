import pytest
from django.urls import reverse

from apps.accounts.models import User


@pytest.mark.django_db
def test_superadmin_can_access_user_management(client):
    superadmin = User.objects.create_superuser(
        email="superadmin@example.com",
        password="SecurePass123!",
    )
    client.force_login(superadmin)

    response = client.get(reverse("accounts:user-management-list"))

    assert response.status_code == 200


@pytest.mark.django_db
def test_admin_cannot_access_user_management(client):
    admin = User.objects.create_user(
        email="admin@example.com",
        password="SecurePass123!",
        role=User.Role.ADMIN,
        is_staff=True,
    )
    client.force_login(admin)

    response = client.get(reverse("accounts:user-management-list"))

    assert response.status_code == 403


@pytest.mark.django_db
def test_superadmin_can_create_regular_user(client):
    superadmin = User.objects.create_superuser(
        email="superadmin@example.com",
        password="SecurePass123!",
    )
    client.force_login(superadmin)

    response = client.post(
        reverse("accounts:user-management-create"),
        {
            "email": "newuser@example.com",
            "role": User.Role.USER,
            "password1": "SecurePass123!",
            "password2": "SecurePass123!",
        },
    )

    assert response.status_code == 302
    created = User.objects.get(email="newuser@example.com")
    assert created.role == User.Role.USER
    assert created.is_superuser is False
    assert created.is_staff is False


@pytest.mark.django_db
def test_superadmin_role_cannot_be_created_from_management_form(client):
    superadmin = User.objects.create_superuser(
        email="superadmin@example.com",
        password="SecurePass123!",
    )
    client.force_login(superadmin)

    response = client.post(
        reverse("accounts:user-management-create"),
        {
            "email": "other-superadmin@example.com",
            "role": User.Role.SUPERADMIN,
            "password1": "SecurePass123!",
            "password2": "SecurePass123!",
        },
    )

    assert response.status_code == 200
    assert not User.objects.filter(email="other-superadmin@example.com").exists()
