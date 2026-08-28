import pytest
from django.urls import reverse


@pytest.mark.parametrize(
    ("route_name", "expected_title"),
    [
        ("portfolio:leadership", "Acompañamiento al Liderazgo de la organización"),
        ("portfolio:retirement", "Jubilación Plena"),
        ("portfolio:consulting", "Mentorías y Consultorías Organizacionales"),
        ("portfolio:model_alpes", "Modelo ALPES"),
    ],
)
def test_public_service_pages_are_available_without_authentication(
    client,
    route_name,
    expected_title,
):
    response = client.get(reverse(route_name))
    content = response.content.decode("utf-8")

    assert response.status_code == 200
    assert expected_title in content
    assert 'name="robots" content="index,follow,max-image-preview:large"' in content
    assert "Conversemos por WhatsApp" in content


@pytest.mark.parametrize(
    "route_name",
    [
        "portfolio:leadership",
        "portfolio:retirement",
        "portfolio:consulting",
        "portfolio:model_alpes",
    ],
)
def test_public_service_pages_expose_canonical_url(client, route_name):
    response = client.get(reverse(route_name), HTTP_HOST="testserver")
    expected_url = f"http://testserver{reverse(route_name)}"

    assert f'rel="canonical" href="{expected_url}"' in response.content.decode("utf-8")


def test_sitemap_lists_public_service_pages(client):
    response = client.get(reverse("portfolio:sitemap"), HTTP_HOST="testserver")
    content = response.content.decode("utf-8")

    assert "http://testserver/servicios/liderazgo/" in content
    assert "http://testserver/servicios/jubilacion-plena/" in content
    assert "http://testserver/servicios/consultoria-organizacional/" in content
    assert "http://testserver/modelo-alpes/" in content
