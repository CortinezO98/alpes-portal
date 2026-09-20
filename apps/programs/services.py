from django.db import transaction
from django.utils import timezone

from .models import Engagement, ParticipantPhase


@transaction.atomic
def ensure_participant_phases(engagement_participant):
    phases = engagement_participant.engagement.program.phases.order_by("order", "id")
    for phase in phases:
        if (
            engagement_participant.engagement.mode == Engagement.Mode.INDIVIDUAL
            and phase.code == "reporte-organizacional"
        ):
            continue
        ParticipantPhase.objects.get_or_create(
            engagement_participant=engagement_participant,
            phase=phase,
        )


def _assessment_phase(assessment):
    if not assessment.engagement_participant_id:
        return None
    return ParticipantPhase.objects.select_related("phase").filter(
        engagement_participant=assessment.engagement_participant,
        phase__code="rueda-vida",
    ).first()


@transaction.atomic
def mark_assessment_phase_started(assessment, actor=None):
    progress = _assessment_phase(assessment)
    if progress is None or progress.status == ParticipantPhase.Status.COMPLETED:
        return
    changed = []
    if progress.status == ParticipantPhase.Status.PENDING:
        progress.status = ParticipantPhase.Status.IN_PROGRESS
        changed.append("status")
    if progress.started_at is None:
        progress.started_at = timezone.now()
        changed.append("started_at")
    if changed:
        changed.append("updated_at")
        progress.save(update_fields=changed)


@transaction.atomic
def mark_assessment_phase_completed(assessment, actor=None):
    progress = _assessment_phase(assessment)
    if progress is None:
        return
    progress.status = ParticipantPhase.Status.COMPLETED
    progress.started_at = progress.started_at or assessment.started_at or timezone.now()
    progress.completed_at = assessment.completed_at or timezone.now()
    progress.completed_by = actor
    progress.save(
        update_fields=(
            "status",
            "started_at",
            "completed_at",
            "completed_by",
            "updated_at",
        )
    )
