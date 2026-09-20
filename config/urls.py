from django.conf import settings
from django.conf.urls.static import static
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
        "cuenta/auth/",
        include("allauth.urls"),
    ),
    path(
        "evaluaciones/",
        include("apps.assessments.urls"),
    ),
    path(
        "reportes/",
        include("apps.reports.urls"),
    ),
    path(
        "programas/",
        include("apps.programs.urls"),
    ),
    path(
        "auditoria/",
        include("apps.audit.urls"),
    ),
]


if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
