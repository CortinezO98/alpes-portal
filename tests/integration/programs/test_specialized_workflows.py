import pytest
from django.core.files.uploadedfile import SimpleUploadedFile

from apps.accounts.models import User
from apps.programs.models import (
    ActionPlanGoal,
    ActionPlanItem,
    DreamChallengeNode,
    Engagement,
    EngagementParticipant,
    ParticipantPhase,
    PhaseArtifact,
    ServiceProgram,
    TransformationSession,
)
from apps.programs.services import ensure_participant_phases, submit_participant_phase


@pytest.fixture
def specialized_setup(db):
    program = ServiceProgram.objects.get(code="jubilacion-plena")
    admin = User.objects.create_superuser(
        email="specialized-admin@example.com",
        password="SecurePass123!",
    )
    participant = User.objects.create_user(
        email="specialized-participant@example.com",
        password="SecurePass123!",
        role=User.Role.USER,
    )
    engagement = Engagement.objects.create(
        title="Jubilación especializada",
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
    return admin, participant, membership


def add_support(progress, user, name="soporte.pdf"):
    return PhaseArtifact.objects.create(
        participant_phase=progress,
        file=SimpleUploadedFile(name, b"PDF test", content_type="application/pdf"),
        original_name=name,
        content_type="application/pdf",
        size_bytes=8,
        uploaded_by=user,
    )


@pytest.mark.django_db
def test_conversations_require_support_and_at_least_one_session(specialized_setup):
    admin, _, membership = specialized_setup
    progress = membership.phase_progress.get(phase__code="conversaciones")
    progress.status = ParticipantPhase.Status.AVAILABLE
    progress.save(update_fields=("status", "updated_at"))

    with pytest.raises(ValueError, match="soporte"):
        submit_participant_phase(progress, admin)

    add_support(progress, admin)

    with pytest.raises(ValueError, match="conversación transformadora"):
        submit_participant_phase(progress, admin)

    TransformationSession.objects.create(
        participant_phase=progress,
        session_date="2026-09-20",
        title="Adaptación al cambio",
        topics="Nueva etapa",
        findings="Hallazgos",
        commitments="Compromisos",
        consultant_appreciation="Lectura profesional",
        created_by=admin,
    )

    submit_participant_phase(progress, admin)
    progress.refresh_from_db()
    assert progress.status == ParticipantPhase.Status.SUBMITTED


@pytest.mark.django_db
def test_dream_map_requires_structured_content(specialized_setup):
    admin, _, membership = specialized_setup
    progress = membership.phase_progress.get(phase__code="mapa-retos-suenos")
    progress.status = ParticipantPhase.Status.AVAILABLE
    progress.save(update_fields=("status", "updated_at"))
    add_support(progress, admin, "mapa.pdf")

    with pytest.raises(ValueError, match="sueño, reto, meta o hito"):
        submit_participant_phase(progress, admin)

    DreamChallengeNode.objects.create(
        participant_phase=progress,
        node_type=DreamChallengeNode.NodeType.DREAM,
        title="Viajar",
        description="Conocer nuevos lugares",
        priority=DreamChallengeNode.Priority.HIGH,
        order=1,
        created_by=admin,
    )

    submit_participant_phase(progress, admin)
    progress.refresh_from_db()
    assert progress.status == ParticipantPhase.Status.SUBMITTED


@pytest.mark.django_db
def test_action_plan_requires_actions_for_every_goal(specialized_setup):
    admin, _, membership = specialized_setup
    progress = membership.phase_progress.get(phase__code="plan-accion")
    progress.status = ParticipantPhase.Status.AVAILABLE
    progress.save(update_fields=("status", "updated_at"))
    add_support(progress, admin, "plan.docx")

    goal = ActionPlanGoal.objects.create(
        participant_phase=progress,
        title="Fortalecer estabilidad financiera",
        description="Meta prioritaria",
        order=1,
        created_by=admin,
    )

    with pytest.raises(ValueError, match="Cada meta debe tener al menos una acción"):
        submit_participant_phase(progress, admin)

    ActionPlanItem.objects.create(
        goal=goal,
        action="Construir presupuesto de retiro",
        indicator="Presupuesto documentado",
        responsible="Participante",
        status=ActionPlanItem.Status.IN_PROGRESS,
        order=1,
        created_by=admin,
    )

    submit_participant_phase(progress, admin)
    progress.refresh_from_db()
    assert progress.status == ParticipantPhase.Status.SUBMITTED
