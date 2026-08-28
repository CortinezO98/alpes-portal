from django.urls import reverse


def test_privacy_page_is_public_but_not_indexable(client):
    response = client.get(reverse("portfolio:privacy"))
    content = response.content.decode()

    assert response.status_code == 200
    assert response.context["seo_index"] is False
    assert "Política de privacidad" in content
    assert "Borrador operativo" in content


def test_data_treatment_page_is_public_but_not_indexable(client):
    response = client.get(reverse("portfolio:data-treatment"))
    content = response.content.decode()

    assert response.status_code == 200
    assert response.context["seo_index"] is False
    assert "Tratamiento de datos personales" in content


def test_legal_pages_expose_canonical_urls(client):
    response = client.get(reverse("portfolio:privacy"), HTTP_HOST="testserver")

    assert response.context["seo_canonical"].endswith(reverse("portfolio:privacy"))


def test_robots_blocks_private_audit_route(client):
    response = client.get(reverse("portfolio:robots"), HTTP_HOST="testserver")

    assert response.status_code == 200
    assert "Disallow: /auditoria/" in response.content.decode()
