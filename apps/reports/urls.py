from django.urls import path

from .views import AnalyticsDashboardView, AssessmentReportDetailView


app_name = "reports"


urlpatterns = [
    path("", AnalyticsDashboardView.as_view(), name="dashboard"),
    path(
        "evaluacion/<int:pk>/",
        AssessmentReportDetailView.as_view(),
        name="assessment-detail",
    ),
]
