from django.urls import path

from .views import (
    EngagementCreateView,
    EngagementDetailView,
    EngagementListView,
    EngagementParticipantCreateView,
    MyEngagementDetailView,
    MyEngagementListView,
    OrganizationCreateView,
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
    path("mis-procesos/", MyEngagementListView.as_view(), name="my-engagements"),
    path(
        "mis-procesos/<int:pk>/",
        MyEngagementDetailView.as_view(),
        name="my-engagement-detail",
    ),
]
