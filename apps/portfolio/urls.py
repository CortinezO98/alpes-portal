from django.urls import path

from .views import PublicHomeView

app_name = "portfolio"

urlpatterns = [
    path("", PublicHomeView.as_view(), name="home"),
]
