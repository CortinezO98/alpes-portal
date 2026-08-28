import pytest
from django.urls import reverse

from apps.accounts.models import User


@pytest.mark.django_db
def test_login_with_email_redirects_to_dashboard(client):
    user = User.objects.create_user(
        email="user@example.com",
        password="SecurePass123!",
        role=User.Role.USER,
    )

    response = client.post(
        reverse("accounts:login"),
        {
            "username": user.email,
            "password": "SecurePass123!",
        },
    )

    assert response.status_code == 302
    assert response.url == reverse("accounts:dashboard")


@pytest.mark.django_db
def test_invalid_login_does_not_authenticate(client):
    response = client.post(
        reverse("accounts:login"),
        {
            "username": "invalid@example.com",
            "password": "wrong-password",
        },
    )

    assert response.status_code == 200
    assert "_auth_user_id" not in client.session


@pytest.mark.django_db
def test_logout_requires_post(client):
    user = User.objects.create_user(
        email="logout@example.com",
        password="SecurePass123!",
    )

    client.force_login(user)

    response = client.get(
        reverse("accounts:logout")
    )

    assert response.status_code == 405


@pytest.mark.django_db
def test_logout_post_ends_session(client):
    user = User.objects.create_user(
        email="logout@example.com",
        password="SecurePass123!",
    )

    client.force_login(user)

    response = client.post(
        reverse("accounts:logout")
    )

    assert response.status_code == 302
    assert "_auth_user_id" not in client.session