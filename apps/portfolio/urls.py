from django.urls import path

from .legal import PublicLegalView
from .views import PublicHomeView, PublicServiceDetailView, robots_txt, sitemap_xml

app_name = "portfolio"

urlpatterns = [
    path("robots.txt", robots_txt, name="robots"),
    path("sitemap.xml", sitemap_xml, name="sitemap"),
    path(
        "privacidad/",
        PublicLegalView.as_view(page_key="privacy"),
        name="privacy",
    ),
    path(
        "tratamiento-de-datos/",
        PublicLegalView.as_view(page_key="data_treatment"),
        name="data-treatment",
    ),
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
