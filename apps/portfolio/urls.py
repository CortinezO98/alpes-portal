from django.urls import path

from .views import PublicHomeView, robots_txt, sitemap_xml

app_name = "portfolio"

urlpatterns = [
    path("robots.txt", robots_txt, name="robots"),
    path("sitemap.xml", sitemap_xml, name="sitemap"),
    path("", PublicHomeView.as_view(), name="home"),
]
