from django.urls import reverse


def test_privacy_page_is_public_but_not_indexable(client):
    response = client.get(reverse("portfolio:privacy"))

    assert response.status_code == 200
    assert response.context["seo_index"] is False
    assert b"PolÃPol\xc3­Pol\xc3\xadtica de privacidad" in response.content
    assert b"Borrador operativo" in response.content


def test_data_treatment_page_is_public_but_not_indexable(client):
    response = client.get(reverse("portfolio:data-treatment"))

    assert response.status_code == 200
    assert response.context["seo_index"] is False
    assert b"Tratamiento de datos personales" in response.content


def test_legal_pages_expose_canonical_urls(client):
    response = client.get(reverse("portfolio:privacy"), HTTP_HOST="testserver")

    assert response.context["seo_canonical"].endswith(reverse("portfolio:privacy"))
