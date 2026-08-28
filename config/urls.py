from django.contrib import admin
from django.urls import include, path


urlpatterns = [
    path("", include("apps.portfolio.urls")),
    path("admin/", admin.site.urls),
    path(
        "cuenta/",
        include("apps.accounts.urls"),
    ),
    path(
        "evaluaciones/",
        include("apps.assessments.urls"),
    ),
    path(
        "reportes/",
        include("apps.reports.urls"),
    ),
]
