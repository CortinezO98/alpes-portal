from django.urls import path

from .views import (
    AnalyticsDashboardView,
    AssessmentReportDetailView,
    DimensionAppreciationUpdateView,
    IndividualProgramReportGenerateView,
    IndividualProgramReportView,
    OrganizationalProgramReportGenerateView,
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
        "programa/proceso/<int:pk>/",
        OrganizationalProgramReportView.as_view(),
        name="program-organizational",
    ),
    path(
        "programa/proceso/<int:pk>/generar/",
        OrganizationalProgramReportGenerateView.as_view(),
        name="program-organizational-generate",
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
