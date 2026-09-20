from django.urls import path

from .views import (
    EngagementCreateView,
    EngagementDetailView,
    EngagementListView,
    EngagementParticipantCreateView,
    EngagementPhaseArtifactCreateView,
    EngagementPhaseCommentCreateView,
    EngagementPhaseDetailView,
    EngagementPhaseReviewView,
    EngagementPhaseSubmitView,
    MyEngagementDetailView,
    MyEngagementListView,
    OrganizationCreateView,
    ParticipantPhaseArtifactCreateView,
    ParticipantPhaseCommentCreateView,
    ParticipantPhaseDetailView,
    ParticipantPhaseReviewView,
    ParticipantPhaseSubmitView,
    ParticipantProgressCompleteView,
    ParticipantProgressUpdateView,
    UnifiedEngagementCreateView,
)

app_name = "programs"

urlpatterns = [
    path("", EngagementListView.as_view(), name="engagement-list"),
    path("organizaciones/nueva/", OrganizationCreateView.as_view(), name="organization-create"),
    path("procesos/nuevo/", UnifiedEngagementCreateView.as_view(), name="engagement-create"),
    path("procesos/<int:pk>/", EngagementDetailView.as_view(), name="engagement-detail"),
    path(
        "procesos/<int:pk>/participantes/agregar/",
        EngagementParticipantCreateView.as_view(),
        name="participant-add",
    ),
    path(
        "procesos/<int:engagement_pk>/participantes/<int:participant_pk>/avance/",
        ParticipantProgressUpdateView.as_view(),
        name="participant-progress-update",
    ),
    path(
        "procesos/<int:engagement_pk>/participantes/<int:participant_pk>/completar/",
        ParticipantProgressCompleteView.as_view(),
        name="participant-progress-complete",
    ),
    path(
        "fases/participante/<int:pk>/",
        ParticipantPhaseDetailView.as_view(),
        name="participant-phase-detail",
    ),
    path(
        "fases/participante/<int:pk>/soportes/",
        ParticipantPhaseArtifactCreateView.as_view(),
        name="participant-phase-artifact",
    ),
    path(
        "fases/participante/<int:pk>/comentarios/",
        ParticipantPhaseCommentCreateView.as_view(),
        name="participant-phase-comment",
    ),
    path(
        "fases/participante/<int:pk>/enviar/",
        ParticipantPhaseSubmitView.as_view(),
        name="participant-phase-submit",
    ),
    path(
        "fases/participante/<int:pk>/revisar/",
        ParticipantPhaseReviewView.as_view(),
        name="participant-phase-review",
    ),
    path(
        "fases/proceso/<int:pk>/",
        EngagementPhaseDetailView.as_view(),
        name="engagement-phase-detail",
    ),
    path(
        "fases/proceso/<int:pk>/soportes/",
        EngagementPhaseArtifactCreateView.as_view(),
        name="engagement-phase-artifact",
    ),
    path(
        "fases/proceso/<int:pk>/comentarios/",
        EngagementPhaseCommentCreateView.as_view(),
        name="engagement-phase-comment",
    ),
    path(
        "fases/proceso/<int:pk>/enviar/",
        EngagementPhaseSubmitView.as_view(),
        name="engagement-phase-submit",
    ),
    path(
        "fases/proceso/<int:pk>/revisar/",
        EngagementPhaseReviewView.as_view(),
        name="engagement-phase-review",
    ),
    path("mis-procesos/", MyEngagementListView.as_view(), name="my-engagements"),
    path(
        "mis-procesos/<int:pk>/",
        MyEngagementDetailView.as_view(),
        name="my-engagement-detail",
    ),
]
