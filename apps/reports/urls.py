from django.urls import path

from .views import AnalyticsDashboardView, AssessmentReportDetailView, DimensionAppreciationUpdateView


app_name = "reports"


urlpatterns = [
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
