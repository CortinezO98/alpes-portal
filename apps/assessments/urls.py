from django.urls import path

from .views import (
    AssessmentAssignView,
    AssessmentDimensionView,
    AssessmentGeneralQuestionsView,
    AssessmentManagementListView,
    AssessmentResultView,
    AssessmentStartView,
    MyAssessmentListView,
)

app_name = "assessments"

urlpatterns = [
    path("", MyAssessmentListView.as_view(), name="my-list"),
    path("gestion/", AssessmentManagementListView.as_view(), name="management-list"),
    path("gestion/asignar/", AssessmentAssignView.as_view(), name="assign"),
    path("<int:pk>/iniciar/", AssessmentStartView.as_view(), name="start"),
    path(
        "<int:pk>/dimension/<int:dimension_pk>/",
        AssessmentDimensionView.as_view(),
        name="dimension",
    ),
    path(
        "<int:pk>/preguntas-finales/",
        AssessmentGeneralQuestionsView.as_view(),
        name="general",
    ),
    path("<int:pk>/resultado/", AssessmentResultView.as_view(), name="result"),
]
