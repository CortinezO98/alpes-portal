from django.urls import path

from .template_views import (
    DimensionCreateView,
    DimensionDeleteView,
    DimensionUpdateView,
    GeneralQuestionCreateView,
    GeneralQuestionUpdateView,
    QuestionDeleteView,
    ScaleQuestionCreateView,
    ScaleQuestionUpdateView,
    TemplateConfigurationDetailView,
    TemplateConfigurationListView,
    TemplateCreateVersionView,
    TemplatePublishView,
)
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
    path(
        "gestion/plantillas/",
        TemplateConfigurationListView.as_view(),
        name="template-list",
    ),
    path(
        "gestion/plantillas/<int:pk>/",
        TemplateConfigurationDetailView.as_view(),
        name="template-detail",
    ),
    path(
        "gestion/plantillas/<int:pk>/nueva-version/",
        TemplateCreateVersionView.as_view(),
        name="template-new-version",
    ),
    path(
        "gestion/plantillas/<int:pk>/publicar/",
        TemplatePublishView.as_view(),
        name="template-publish",
    ),
    path(
        "gestion/plantillas/<int:template_pk>/dimensiones/nueva/",
        DimensionCreateView.as_view(),
        name="dimension-create",
    ),
    path(
        "gestion/dimensiones/<int:pk>/editar/",
        DimensionUpdateView.as_view(),
        name="dimension-edit",
    ),
    path(
        "gestion/dimensiones/<int:pk>/eliminar/",
        DimensionDeleteView.as_view(),
        name="dimension-delete",
    ),
    path(
        "gestion/dimensiones/<int:dimension_pk>/preguntas/nueva/",
        ScaleQuestionCreateView.as_view(),
        name="scale-question-create",
    ),
    path(
        "gestion/preguntas/<int:pk>/editar/",
        ScaleQuestionUpdateView.as_view(),
        name="scale-question-edit",
    ),
    path(
        "gestion/plantillas/<int:template_pk>/preguntas-abiertas/nueva/",
        GeneralQuestionCreateView.as_view(),
        name="general-question-create",
    ),
    path(
        "gestion/preguntas-abiertas/<int:pk>/editar/",
        GeneralQuestionUpdateView.as_view(),
        name="general-question-edit",
    ),
    path(
        "gestion/preguntas/<int:pk>/eliminar/",
        QuestionDeleteView.as_view(),
        name="question-delete",
    ),
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
