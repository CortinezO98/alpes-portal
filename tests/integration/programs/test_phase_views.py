import pytest
from django.core.files.uploadedfile import SimpleUploadedFile
from django.urls import reverse
from django.utils import timezone

from apps.accounts.models import User
from apps.assessments.models import Assessment, AssessmentTemplate
from apps.programs.models import (
    ActionPlanGoal,
    ActionPlanItem,
    DreamChallengeNode,
    Engagement,
    EngagementParticipant,
    ParticipantPhase,
    PhaseArtifact,
    PhaseComment,
    ServiceProgram,
    TransformationSession,
)
from apps.programs.services import ensure_participant_phases


@pytest.fixture
def phase_views_setup(db):
    program = ServiceProgram.objects.get(code="jubilacion-plena")
    admin = User.objects.create_superuser(
        email="phase-admin@example.com",
        password="SecurePass123!",
    )
    participant = User.objects.create_user(
        email="phase-participant@example.com",
        password="SecurePass123!",
        role=User.Role.USER,
    )
    outsider = User.objects.create_user(
        email="phase-outsider@example.com",
        password="SecurePass123!",
        role=User.Role.USER,
    )
    engagement = Engagement.objects.create(
        title="Cobertura de fases",
        program=program,
        mode=Engagement.Mode.INDIVIDUAL,
        consultant=admin,
        status=Engagement.Status.ACTIVE,
    )
    membership = EngagementParticipant.objects.create(
        engagement=engagement,
        participant=participant,
    )
    ensure_participant_phases(membership)
    return admin, participant, outsider, engagement, membership


def make_available(membership, code):
    progress = membership.phase_progress.get(phase__code=code)
    progress.status = ParticipantPhase.Status.AVAILABLE
    progress.save(update_fields=("status", "updated_at"))
    return progress


def pdf_upload(name="soporte.pdf"):
    return SimpleUploadedFile(
        name,
        b"%PDF-1.4 test support",
        content_type="application/pdf",
    )


@pytest.mark.django_db
def test_participant_can_open_own_workspaces_and_outsider_cannot(client, phase_views_setup):
    admin, participant, outsider, _, membership = phase_views_setup

    for code, expected_key in (
        ("charla-inicial", "consultant_experience_record"),
        ("conversaciones", "transformation_sessions"),
        ("mapa-retos-suenos", "dream_nodes"),
        ("plan-accion", "action_goals"),
    ):
        progress = membership.phase_progress.get(phase__code=code)

        client.force_login(participant)
        response = client.get(
            reverse("programs:participant-phase-detail", kwargs={"pk": progress.pk})
        )
        assert response.status_code == 200
        assert response.context["workspace_scope"] == "participant"
        assert response.context["is_program_admin"] is False
        assert expected_key in response.context

        client.force_login(admin)
        response = client.get(
            reverse("programs:participant-phase-detail", kwargs={"pk": progress.pk})
        )
        assert response.status_code == 200
        assert response.context["is_program_admin"] is True

    progress = membership.phase_progress.get(phase__code="conversaciones")
    client.force_login(outsider)
    response = client.get(
        reverse("programs:participant-phase-detail", kwargs={"pk": progress.pk})
    )
    assert response.status_code == 404


@pytest.mark.django_db
def test_participant_support_comment_submit_and_admin_review_flow(client, phase_views_setup):
    admin, participant, _, _, membership = phase_views_setup
    progress = make_available(membership, "conversaciones")

    client.force_login(participant)
    response = client.post(
        reverse("programs:transformation-session-create", kwargs={"pk": progress.pk}),
        {
            "session_date": "2026-09-20",
            "title": "Cambio de etapa",
            "topics": "Propósito",
            "findings": "Nuevas prioridades",
            "commitments": "Definir próximos pasos",
            "consultant_appreciation": "No debe conservarse para participante",
        },
    )
    assert response.status_code == 302
    session = TransformationSession.objects.get(participant_phase=progress)
    assert session.consultant_appreciation == ""

    response = client.post(
        reverse("programs:participant-phase-artifact", kwargs={"pk": progress.pk}),
        {"file": pdf_upload()},
    )
    assert response.status_code == 302
    artifact = PhaseArtifact.objects.get(participant_phase=progress)
    assert artifact.uploaded_by == participant
    assert artifact.content_type == "application/pdf"

    response = client.post(
        reverse("programs:participant-phase-comment", kwargs={"pk": progress.pk}),
        {"body": "Esta conversación me ayudó a priorizar.", "is_internal": "on"},
    )
    assert response.status_code == 302
    comment = PhaseComment.objects.get(participant_phase=progress)
    assert comment.author == participant
    assert comment.is_internal is False

    response = client.post(
        reverse("programs:participant-phase-submit", kwargs={"pk": progress.pk})
    )
    assert response.status_code == 302
    progress.refresh_from_db()
    assert progress.status == ParticipantPhase.Status.SUBMITTED

    client.force_login(admin)
    response = client.post(
        reverse("programs:participant-phase-review", kwargs={"pk": progress.pk}),
        {"action": "reopen", "review_note": "Agregar mayor detalle."},
    )
    assert response.status_code == 302
    progress.refresh_from_db()
    assert progress.status == ParticipantPhase.Status.REOPENED

    response = client.post(
        reverse("programs:participant-phase-comment", kwargs={"pk": progress.pk}),
        {"body": "Observación interna del consultor.", "is_internal": "on"},
    )
    assert response.status_code == 302
    internal = PhaseComment.objects.filter(
        participant_phase=progress,
        author=admin,
    ).latest("id")
    assert internal.is_internal is True

    progress.status = ParticipantPhase.Status.SUBMITTED
    progress.save(update_fields=("status", "updated_at"))
    response = client.post(
        reverse("programs:participant-phase-review", kwargs={"pk": progress.pk}),
        {"action": "approve", "review_note": "Validado."},
    )
    assert response.status_code == 302
    progress.refresh_from_db()
    assert progress.status == ParticipantPhase.Status.COMPLETED


@pytest.mark.django_db
def test_specialized_content_can_be_updated_and_participant_cannot_replace_appreciations(
    client, phase_views_setup
):
    admin, participant, _, _, membership = phase_views_setup

    conversation = make_available(membership, "conversaciones")
    session = TransformationSession.objects.create(
        participant_phase=conversation,
        session_date="2026-09-20",
        title="Sesión original",
        topics="Tema",
        findings="Hallazgo",
        commitments="Compromiso",
        consultant_appreciation="Apreciación reservada",
        created_by=admin,
    )
    client.force_login(participant)
    response = client.post(
        reverse(
            "programs:transformation-session-update",
            kwargs={"pk": conversation.pk, "session_pk": session.pk},
        ),
        {
            "session_date": "2026-09-21",
            "title": "Sesión actualizada",
            "topics": "Tema actualizado",
            "findings": "Hallazgo actualizado",
            "commitments": "Compromiso actualizado",
            "consultant_appreciation": "Intento de reemplazo",
        },
    )
    assert response.status_code == 302
    session.refresh_from_db()
    assert session.title == "Sesión actualizada"
    assert session.consultant_appreciation == "Apreciación reservada"

    dream_map = make_available(membership, "mapa-retos-suenos")
    node = DreamChallengeNode.objects.create(
        participant_phase=dream_map,
        node_type=DreamChallengeNode.NodeType.DREAM,
        title="Viajar",
        description="Descripción inicial",
        priority=DreamChallengeNode.Priority.HIGH,
        order=1,
        created_by=admin,
    )
    response = client.post(
        reverse(
            "programs:dream-node-update",
            kwargs={"pk": dream_map.pk, "node_pk": node.pk},
        ),
        {
            "parent": "",
            "node_type": DreamChallengeNode.NodeType.GOAL,
            "title": "Viajar con planificación",
            "description": "Descripción actualizada",
            "priority": DreamChallengeNode.Priority.HIGH,
            "target_date": "2027-12-31",
        },
    )
    assert response.status_code == 302
    node.refresh_from_db()
    assert node.title == "Viajar con planificación"

    action_plan = make_available(membership, "plan-accion")
    goal = ActionPlanGoal.objects.create(
        participant_phase=action_plan,
        title="Meta original",
        description="Descripción",
        order=1,
        created_by=admin,
    )
    item = ActionPlanItem.objects.create(
        goal=goal,
        action="Acción original",
        indicator="Indicador",
        responsible="Participante",
        status=ActionPlanItem.Status.PENDING,
        consultant_appreciation="Apreciación profesional",
        order=1,
        created_by=admin,
    )

    response = client.post(
        reverse(
            "programs:action-goal-update",
            kwargs={"pk": action_plan.pk, "goal_pk": goal.pk},
        ),
        {
            "title": "Meta actualizada",
            "description": "Nueva descripción",
            "target_date": "2027-06-30",
        },
    )
    assert response.status_code == 302
    goal.refresh_from_db()
    assert goal.title == "Meta actualizada"

    response = client.post(
        reverse(
            "programs:action-item-update",
            kwargs={"pk": action_plan.pk, "item_pk": item.pk},
        ),
        {
            "action": "Acción actualizada",
            "indicator": "Indicador actualizado",
            "responsible": "Participante",
            "due_date": "2026-12-31",
            "status": ActionPlanItem.Status.IN_PROGRESS,
            "consultant_appreciation": "Intento de reemplazo",
        },
    )
    assert response.status_code == 302
    item.refresh_from_db()
    assert item.action == "Acción actualizada"
    assert item.consultant_appreciation == "Apreciación profesional"


@pytest.mark.django_db
def test_manual_phase_adjustment_requires_reason_and_updates_roadmap(client, phase_views_setup):
    admin, _, _, engagement, membership = phase_views_setup
    target = membership.phase_progress.get(phase__code="mapa-retos-suenos")
    client.force_login(admin)

    url = reverse(
        "programs:participant-progress-update",
        kwargs={
            "engagement_pk": engagement.pk,
            "participant_pk": membership.pk,
        },
    )
    response = client.post(url, {"phase_progress_id": target.pk, "manual_reason": ""})
    assert response.status_code == 302
    target.refresh_from_db()
    assert target.status == ParticipantPhase.Status.PENDING

    response = client.post(
        url,
        {
            "phase_progress_id": target.pk,
            "manual_reason": "Ajuste acordado con el participante.",
        },
    )
    assert response.status_code == 302

    target.refresh_from_db()
    assert target.status == ParticipantPhase.Status.IN_PROGRESS
    assert membership.phase_progress.filter(
        phase__order__lt=target.phase.order,
        status=ParticipantPhase.Status.COMPLETED,
    ).count() == target.phase.order - 1
    assert PhaseComment.objects.filter(
        participant_phase=target,
        is_internal=True,
        body__contains="Ajuste manual",
    ).exists()


@pytest.mark.django_db
def test_complete_participant_marks_all_phases_completed(client, phase_views_setup):
    admin, _, _, engagement, membership = phase_views_setup
    client.force_login(admin)

    response = client.post(
        reverse(
            "programs:participant-progress-complete",
            kwargs={
                "engagement_pk": engagement.pk,
                "participant_pk": membership.pk,
            },
        )
    )
    assert response.status_code == 302
    assert not membership.phase_progress.exclude(
        status=ParticipantPhase.Status.COMPLETED
    ).exists()


@pytest.mark.django_db
def test_my_engagements_and_roadmap_are_scoped_to_owner(client, phase_views_setup):
    admin, participant, outsider, _, membership = phase_views_setup

    client.force_login(participant)
    response = client.get(reverse("programs:my-engagements"))
    assert response.status_code == 200
    assert membership in list(response.context["participations"])

    response = client.get(
        reverse("programs:my-engagement-detail", kwargs={"pk": membership.pk})
    )
    assert response.status_code == 200

    response = client.get(reverse("programs:roadmap-detail", kwargs={"pk": membership.pk}))
    assert response.status_code == 200
    assert response.context["is_program_admin"] is False

    client.force_login(admin)
    response = client.get(reverse("programs:roadmap-detail", kwargs={"pk": membership.pk}))
    assert response.status_code == 200
    assert response.context["is_program_admin"] is True

    client.force_login(outsider)
    response = client.get(reverse("programs:roadmap-detail", kwargs={"pk": membership.pk}))
    assert response.status_code == 404


@pytest.mark.django_db
def test_locked_phase_rejects_specialized_edits_and_invalid_review(client, phase_views_setup):
    admin, participant, _, _, membership = phase_views_setup
    conversation = membership.phase_progress.get(phase__code="conversaciones")
    assert conversation.status == ParticipantPhase.Status.PENDING

    client.force_login(participant)
    response = client.post(
        reverse("programs:transformation-session-create", kwargs={"pk": conversation.pk}),
        {
            "session_date": "2026-09-20",
            "title": "No debe guardarse",
            "topics": "Tema",
            "findings": "Hallazgo",
            "commitments": "Compromiso",
        },
    )
    assert response.status_code == 302
    assert not TransformationSession.objects.filter(
        participant_phase=conversation
    ).exists()

    client.force_login(admin)
    response = client.post(
        reverse("programs:participant-phase-review", kwargs={"pk": conversation.pk}),
        {"action": "invalid", "review_note": ""},
    )
    assert response.status_code == 302
    conversation.refresh_from_db()
    assert conversation.status == ParticipantPhase.Status.PENDING


@pytest.mark.django_db
def test_admin_can_unlock_pending_phase_from_workspace(client, phase_views_setup):
    admin, participant, _, engagement, membership = phase_views_setup
    progress = membership.phase_progress.get(phase__code="mapa-retos-suenos")
    assert progress.status == ParticipantPhase.Status.PENDING

    client.force_login(admin)
    detail = client.get(
        reverse("programs:participant-phase-detail", kwargs={"pk": progress.pk})
    )
    assert detail.status_code == 200
    assert b"Habilitar esta fase" in detail.content

    response = client.post(
        reverse(
            "programs:participant-progress-update",
            kwargs={
                "engagement_pk": engagement.pk,
                "participant_pk": membership.pk,
            },
        ),
        {
            "phase_progress_id": progress.pk,
            "manual_reason": "Habilitación manual desde la fase Mapa de retos y sueños",
        },
    )
    assert response.status_code == 302

    progress.refresh_from_db()
    assert progress.status == ParticipantPhase.Status.IN_PROGRESS

    client.force_login(participant)
    detail = client.get(
        reverse("programs:participant-phase-detail", kwargs={"pk": progress.pk})
    )
    assert detail.status_code == 200
    assert b"Agregar soporte" in detail.content


@pytest.mark.django_db
def test_rueda_phase_reconciles_single_completed_unlinked_assessment(
    client, phase_views_setup
):
    admin, participant, _, _, membership = phase_views_setup
    template = AssessmentTemplate.objects.filter(
        slug__startswith="alpes-jubilacion-plena"
    ).order_by("-version", "-id").first()
    assert template is not None

    charla = membership.phase_progress.get(phase__code="charla-inicial")
    charla.status = ParticipantPhase.Status.COMPLETED
    charla.save(update_fields=("status", "updated_at"))

    rueda = membership.phase_progress.get(phase__code="rueda-vida")
    rueda.status = ParticipantPhase.Status.IN_PROGRESS
    rueda.save(update_fields=("status", "updated_at"))

    assessment = Assessment.objects.create(
        template=template,
        participant=participant,
        created_by=admin,
        status=Assessment.Status.COMPLETED,
        started_at=timezone.now(),
        completed_at=timezone.now(),
    )
    assert assessment.engagement_participant_id is None

    client.force_login(admin)
    response = client.get(
        reverse("programs:participant-phase-detail", kwargs={"pk": rueda.pk})
    )
    assert response.status_code == 200

    assessment.refresh_from_db()
    rueda.refresh_from_db()
    conversation = membership.phase_progress.get(phase__code="conversaciones")

    assert assessment.engagement_participant_id == membership.pk
    assert rueda.status == ParticipantPhase.Status.COMPLETED
    assert conversation.status == ParticipantPhase.Status.AVAILABLE
    assert response.context["assessment_reconciliation"]["status"] == "linked_completed"


@pytest.mark.django_db
def test_rueda_phase_does_not_guess_when_multiple_completed_assessments_exist(
    client, phase_views_setup
):
    admin, participant, _, _, membership = phase_views_setup
    template = AssessmentTemplate.objects.filter(
        slug__startswith="alpes-jubilacion-plena"
    ).order_by("-version", "-id").first()
    assert template is not None

    rueda = membership.phase_progress.get(phase__code="rueda-vida")
    rueda.status = ParticipantPhase.Status.IN_PROGRESS
    rueda.save(update_fields=("status", "updated_at"))

    for _ in range(2):
        Assessment.objects.create(
            template=template,
            participant=participant,
            created_by=admin,
            status=Assessment.Status.COMPLETED,
            started_at=timezone.now(),
            completed_at=timezone.now(),
        )

    client.force_login(admin)
    response = client.get(
        reverse("programs:participant-phase-detail", kwargs={"pk": rueda.pk})
    )
    assert response.status_code == 200
    assert response.context["assessment_reconciliation"]["status"] == "ambiguous"
    assert Assessment.objects.filter(
        participant=participant,
        engagement_participant=membership,
    ).count() == 0

    rueda.refresh_from_db()
    assert rueda.status == ParticipantPhase.Status.IN_PROGRESS
