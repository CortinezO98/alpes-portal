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


@pytest.mark.django_db
def test_superadmin_can_edit_regular_user_and_sync_staff(client):
    superadmin = User.objects.create_superuser(
        email="superadmin@example.com",
        password="SecurePass123!",
    )
    user = User.objects.create_user(
        email="user@example.com",
        password="SecurePass123!",
        role=User.Role.USER,
    )
    client.force_login(superadmin)

    response = client.post(
        reverse("accounts:user-management-edit", args=[user.pk]),
        {
            "email": "admin-updated@example.com",
            "role": User.Role.ADMIN,
        },
    )

    assert response.status_code == 302
    user.refresh_from_db()
    assert user.email == "admin-updated@example.com"
    assert user.role == User.Role.ADMIN
    assert user.is_staff is True
    assert user.is_superuser is False


@pytest.mark.django_db
def test_superadmin_account_cannot_be_edited_from_management(client):
    superadmin = User.objects.create_superuser(
        email="superadmin@example.com",
        password="SecurePass123!",
    )
    client.force_login(superadmin)

    response = client.get(
        reverse("accounts:user-management-edit", args=[superadmin.pk])
    )

    assert response.status_code == 403


@pytest.mark.django_db
def test_superadmin_can_deactivate_regular_user(client):
    superadmin = User.objects.create_superuser(
        email="superadmin@example.com",
        password="SecurePass123!",
    )
    user = User.objects.create_user(
        email="user@example.com",
        password="SecurePass123!",
        role=User.Role.USER,
    )
    client.force_login(superadmin)

    response = client.post(
        reverse("accounts:user-management-toggle-status", args=[user.pk])
    )

    assert response.status_code == 302
    user.refresh_from_db()
    assert user.is_active is False


@pytest.mark.django_db
def test_superadmin_cannot_deactivate_own_account(client):
    superadmin = User.objects.create_superuser(
        email="superadmin@example.com",
        password="SecurePass123!",
    )
    client.force_login(superadmin)

    response = client.post(
        reverse("accounts:user-management-toggle-status", args=[superadmin.pk])
    )

    assert response.status_code == 403
    superadmin.refresh_from_db()
    assert superadmin.is_active is True
