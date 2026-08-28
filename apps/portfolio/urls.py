from django.urls import path

from .views import PublicHomeView, PublicServiceDetailView, robots_txt, sitemap_xml

app_name = "portfolio"

urlpatterns = [
    path("robots.txt", robots_txt, name="robots"),
    path("sitemap.xml", sitemap_xml, name="sitemap"),
    path(
        "servicios/liderazgo/",
        PublicServiceDetailView.as_view(page_key="leadership"),
        name="leadership",
    ),
    path(
        "servicios/jubilacion-plena/",
        PublicServiceDetailView.as_view(page_key="retirement"),
        name="retirement",
    ),
    path(
        "servicios/consultoria-organizacional/",
        PublicServiceDetailView.as_view(page_key="consulting"),
        name="consulting",
    ),
    path(
        "modelo-alpes/",
        PublicServiceDetailView.as_view(page_key="alpes"),
        name="model_alpes",
    ),
    path("", PublicHomeView.as_view(), name="home"),
]
