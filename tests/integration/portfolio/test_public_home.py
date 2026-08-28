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


def test_public_home_exposes_seo_metadata(client):
    response = client.get(reverse("portfolio:home"))
    content = response.content.decode("utf-8")

    assert 'name="robots" content="index,follow,max-image-preview:large"' in content
    assert 'name="description"' in content
    assert 'property="og:title"' in content
    assert 'property="og:description"' in content
    assert 'rel="canonical" href="http://testserver/"' in content
    assert 'rel="icon"' in content


def test_public_home_exposes_whatsapp_contact(client):
    response = client.get(reverse("portfolio:home"))
    content = response.content.decode("utf-8")

    assert "https://wa.me/573107426028" in content
    assert "Escribir por WhatsApp" in content


def test_robots_txt_allows_public_site_and_blocks_private_routes(client):
    response = client.get(reverse("portfolio:robots"))
    content = response.content.decode("utf-8")

    assert response.status_code == 200
    assert response["Content-Type"].startswith("text/plain")
    assert "Allow: /" in content
    assert "Disallow: /cuenta/" in content
    assert "Disallow: /evaluaciones/" in content
    assert "Disallow: /reportes/" in content
    assert "Sitemap: http://testserver/sitemap.xml" in content


def test_sitemap_xml_lists_public_home(client):
    response = client.get(reverse("portfolio:sitemap"))
    content = response.content.decode("utf-8")

    assert response.status_code == 200
    assert response["Content-Type"].startswith("application/xml")
    assert "<loc>http://testserver/</loc>" in content
    assert "<priority>1.0</priority>" in content
