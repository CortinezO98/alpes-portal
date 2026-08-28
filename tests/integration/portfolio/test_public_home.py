from django.urls import reverse


def test_public_home_is_available_without_authentication(client):
    response = client.get(reverse("portfolio:home"))

    assert response.status_code == 200


def test_public_home_exposes_core_portfolio_services(client):
    response = client.get(reverse("portfolio:home"))
    content = response.content.decode("utf-8")

    assert "Acompañamiento al Liderazgo de la organización" in content
    assert "Jubilación Plena" in content
    assert "Mentorías y Consultorías Organizacionales" in content
    assert "Modelo ALPES" in content


def test_public_home_keeps_private_access_secondary(client):
    response = client.get(reverse("portfolio:home"))

    assert reverse("accounts:login") in response.content.decode("utf-8")
