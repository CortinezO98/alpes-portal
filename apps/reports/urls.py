from django.urls import path

from .views import (
    AnalyticsDashboardView,
    AssessmentReportDetailView,
    DimensionAppreciationUpdateView,
    IndividualProgramReportGenerateView,
    IndividualProgramReportPdfView,
    IndividualProgramReportView,
    OrganizationalProgramReportGenerateView,
    OrganizationalProgramReportPdfView,
    OrganizationalProgramReportView,
)


app_name = "reports"


urlpatterns = [
    path(
        "programa/participante/<int:pk>/",
        IndividualProgramReportView.as_view(),
        name="program-individual",
    ),
    path(
        "programa/participante/<int:pk>/generar/",
        IndividualProgramReportGenerateView.as_view(),
        name="program-individual-generate",
    ),
    path(
        "programa/participante/<int:pk>/version/<int:version>/pdf/",
        IndividualProgramReportPdfView.as_view(),
        name="program-individual-pdf",
    ),
    path(
        "programa/proceso/<int:pk>/",
        OrganizationalProgramReportView.as_view(),
        name="program-organizational",
    ),
    path(
        "programa/proceso/<int:pk>/generar/",
        OrganizationalProgramReportGenerateView.as_view(),
        name="program-organizational-generate",
    ),
    path(
        "programa/proceso/<int:pk>/version/<int:version>/pdf/",
        OrganizationalProgramReportPdfView.as_view(),
        name="program-organizational-pdf",
    ),
    path("", AnalyticsDashboardView.as_view(), name="dashboard"),
    path(
        "evaluacion/<int:pk>/",
        AssessmentReportDetailView.as_view(),
        name="assessment-detail",
    ),
    path(
        "evaluacion/<int:assessment_pk>/dimension/<int:dimension_pk>/apreciacion/",
        DimensionAppreciationUpdateView.as_view(),
        name="dimension-appreciation",
    ),
]
