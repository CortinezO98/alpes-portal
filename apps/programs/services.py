from django.db import transaction
from django.utils import timezone

from .models import (
    Engagement,
    EngagementParticipant,
    EngagementPhase,
    Organization,
    ParticipantPhase,
    ProgramPhase,
)


@transaction.atomic
def ensure_engagement_phases(engagement):
    phases = engagement.program.phases.filter(
        scope=ProgramPhase.Scope.ENGAGEMENT
    ).order_by("order", "id")
    for phase in phases:
        if engagement.mode == Engagement.Mode.INDIVIDUAL:
            continue
        EngagementPhase.objects.get_or_create(
            engagement=engagement,
            phase=phase,
        )


@transaction.atomic
def ensure_participant_phases(engagement_participant):
    phases = engagement_participant.engagement.program.phases.filter(
        scope=ProgramPhase.Scope.PARTICIPANT
    ).order_by("order", "id")

    progress_items = []
    for phase in phases:
        progress, _ = ParticipantPhase.objects.get_or_create(
            engagement_participant=engagement_participant,
            phase=phase,
        )
        progress_items.append(progress)

    if progress_items and not any(
        item.status
        in {
            ParticipantPhase.Status.AVAILABLE,
            ParticipantPhase.Status.IN_PROGRESS,
            ParticipantPhase.Status.SUBMITTED,
            ParticipantPhase.Status.UNDER_REVIEW,
            ParticipantPhase.Status.COMPLETED,
            ParticipantPhase.Status.REOPENED,
        }
        for item in progress_items
    ):
        first = progress_items[0]
        first.status = ParticipantPhase.Status.AVAILABLE
        first.save(update_fields=("status", "updated_at"))

    ensure_engagement_phases(engagement_participant.engagement)


def _participant_next_progress(progress):
    return (
        progress.engagement_participant.phase_progress.filter(
            phase__scope=ProgramPhase.Scope.PARTICIPANT,
            phase__order__gt=progress.phase.order,
        )
        .select_related("phase")
        .order_by("phase__order", "id")
        .first()
    )


def _unlock_after_participant_completion(progress):
    ordered_progress = list(
        progress.engagement_participant.phase_progress.filter(
            phase__scope=ProgramPhase.Scope.PARTICIPANT
        )
        .select_related("phase")
        .order_by("phase__order", "id")
    )
    next_actionable = next(
        (
            item
            for item in ordered_progress
            if item.status != ParticipantPhase.Status.COMPLETED
        ),
        None,
    )

    if (
        next_actionable
        and next_actionable.status == ParticipantPhase.Status.PENDING
    ):
        next_actionable.status = ParticipantPhase.Status.AVAILABLE
        next_actionable.save(update_fields=("status", "updated_at"))

    if progress.phase.code == "reporte-individual":
        engagement = progress.engagement_participant.engagement

        if engagement.mode == Engagement.Mode.INDIVIDUAL:
            engagement.status = Engagement.Status.COMPLETED
            engagement.end_date = engagement.end_date or timezone.localdate()
            engagement.save(update_fields=("status", "end_date", "updated_at"))
            return

        individual_report_phase = progress.phase
        incomplete_exists = ParticipantPhase.objects.filter(
            engagement_participant__engagement=engagement,
            engagement_participant__is_active=True,
            phase=individual_report_phase,
        ).exclude(status=ParticipantPhase.Status.COMPLETED).exists()

        if not incomplete_exists:
            org_progress = (
                engagement.phase_progress.filter(
                    phase__scope=ProgramPhase.Scope.ENGAGEMENT
                )
                .select_related("phase")
                .order_by("phase__order", "id")
                .first()
            )
            if org_progress and org_progress.status == ParticipantPhase.Status.PENDING:
                org_progress.status = ParticipantPhase.Status.AVAILABLE
                org_progress.save(update_fields=("status", "updated_at"))


@transaction.atomic
def submit_participant_phase(progress, actor):
    if progress.status in {
        ParticipantPhase.Status.PENDING,
        ParticipantPhase.Status.COMPLETED,
        ParticipantPhase.Status.SUBMITTED,
        ParticipantPhase.Status.UNDER_REVIEW,
    }:
        raise ValueError("Esta fase no está disponible para envío en su estado actual.")

    if (
        progress.phase.requires_artifact
        and not progress.artifacts.exists()
        and progress.phase.code != "rueda-vida"
    ):
        raise ValueError("Esta fase requiere al menos un soporte antes de enviarla.")

    progress.started_at = progress.started_at or timezone.now()
    if progress.phase.requires_review:
        progress.status = ParticipantPhase.Status.SUBMITTED
    else:
        progress.status = ParticipantPhase.Status.COMPLETED
        progress.completed_at = timezone.now()
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

    if progress.status == ParticipantPhase.Status.COMPLETED:
        _unlock_after_participant_completion(progress)
    return progress


@transaction.atomic
def review_participant_phase(progress, *, actor, approve, note=""):
    if progress.status not in {
        ParticipantPhase.Status.SUBMITTED,
        ParticipantPhase.Status.UNDER_REVIEW,
    }:
        raise ValueError("La fase debe estar enviada a revisión antes de aprobarla o reabrirla.")

    if note:
        progress.notes = note

    if approve:
        progress.status = ParticipantPhase.Status.COMPLETED
        progress.started_at = progress.started_at or timezone.now()
        progress.completed_at = timezone.now()
        progress.completed_by = actor
    else:
        progress.status = ParticipantPhase.Status.REOPENED
        progress.completed_at = None
        progress.completed_by = None

    progress.save(
        update_fields=(
            "status",
            "started_at",
            "completed_at",
            "completed_by",
            "notes",
            "updated_at",
        )
    )

    if approve:
        _unlock_after_participant_completion(progress)
    return progress


@transaction.atomic
def submit_engagement_phase(progress, actor):
    if progress.status in {
        ParticipantPhase.Status.PENDING,
        ParticipantPhase.Status.COMPLETED,
        ParticipantPhase.Status.SUBMITTED,
        ParticipantPhase.Status.UNDER_REVIEW,
    }:
        raise ValueError("Esta fase organizacional no está disponible para envío.")

    if progress.phase.requires_artifact and not progress.artifacts.exists():
        raise ValueError("Esta fase requiere al menos un soporte antes de enviarla.")

    progress.started_at = progress.started_at or timezone.now()
    if progress.phase.requires_review:
        progress.status = ParticipantPhase.Status.SUBMITTED
    else:
        progress.status = ParticipantPhase.Status.COMPLETED
        progress.completed_at = timezone.now()
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

    if progress.status == ParticipantPhase.Status.COMPLETED:
        progress.engagement.status = Engagement.Status.COMPLETED
        progress.engagement.end_date = progress.engagement.end_date or timezone.localdate()
        progress.engagement.save(update_fields=("status", "end_date", "updated_at"))

    return progress


@transaction.atomic
def review_engagement_phase(progress, *, actor, approve, note=""):
    if progress.status not in {
        ParticipantPhase.Status.SUBMITTED,
        ParticipantPhase.Status.UNDER_REVIEW,
    }:
        raise ValueError("La fase organizacional debe estar enviada a revisión.")

    if note:
        progress.notes = note

    if approve:
        progress.status = ParticipantPhase.Status.COMPLETED
        progress.started_at = progress.started_at or timezone.now()
        progress.completed_at = timezone.now()
        progress.completed_by = actor
    else:
        progress.status = ParticipantPhase.Status.REOPENED
        progress.completed_at = None
        progress.completed_by = None

    progress.save(
        update_fields=(
            "status",
            "started_at",
            "completed_at",
            "completed_by",
            "notes",
            "updated_at",
        )
    )

    if approve and not progress.engagement.phase_progress.exclude(
        status=ParticipantPhase.Status.COMPLETED
    ).exists():
        progress.engagement.status = Engagement.Status.COMPLETED
        progress.engagement.end_date = progress.engagement.end_date or timezone.localdate()
        progress.engagement.save(update_fields=("status", "end_date", "updated_at"))

    return progress


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
    if progress.status in {
        ParticipantPhase.Status.PENDING,
        ParticipantPhase.Status.AVAILABLE,
        ParticipantPhase.Status.REOPENED,
    }:
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
    _unlock_after_participant_completion(progress)


@transaction.atomic
def create_engagement_bundle(*, cleaned_data, actor):
    """Create the complete onboarding bundle as one atomic business operation."""
    from apps.accounts.models import User
    from apps.assessments.models import Assessment

    organization = cleaned_data.get("organization")
    if (
        cleaned_data["mode"] == Engagement.Mode.ORGANIZATIONAL
        and cleaned_data.get("create_organization")
    ):
        organization = Organization.objects.create(
            name=cleaned_data["organization_name"].strip(),
            tax_id=(cleaned_data.get("organization_tax_id") or "").strip(),
            contact_name=(cleaned_data.get("organization_contact_name") or "").strip(),
            contact_email=(cleaned_data.get("organization_contact_email") or "").strip(),
        )

    program = cleaned_data["program"]
    title = (cleaned_data.get("title") or "").strip()
    if not title:
        context_name = organization.name if organization is not None else "Individual"
        title = f"{program.name} · {context_name} · {timezone.localdate().year}"

    engagement = Engagement(
        title=title,
        program=program,
        mode=cleaned_data["mode"],
        organization=organization,
        consultant=actor,
        status=cleaned_data["status"],
        start_date=cleaned_data.get("start_date"),
        end_date=cleaned_data.get("end_date"),
        notes=(cleaned_data.get("notes") or "").strip(),
    )
    engagement.full_clean()
    engagement.save()
    ensure_engagement_phases(engagement)

    users = list(cleaned_data.get("participants") or [])
    for row in cleaned_data.get("new_participants_json") or []:
        users.append(
            User.objects.create_user(
                email=row["email"],
                password=row["password"],
                first_name=row["first_name"],
                last_name=row["last_name"],
                role=User.Role.USER,
                is_active=True,
            )
        )

    template = cleaned_data.get("assessment_template")
    assessments_created = 0
    memberships = []

    for user in users:
        membership = EngagementParticipant.objects.create(
            engagement=engagement,
            participant=user,
        )
        memberships.append(membership)
        ensure_participant_phases(membership)

        if cleaned_data.get("assign_assessment") and template:
            _, was_created = Assessment.objects.get_or_create(
                template=template,
                participant=user,
                engagement_participant=membership,
                defaults={
                    "created_by": actor,
                    "status": Assessment.Status.DRAFT,
                },
            )
            assessments_created += int(was_created)

    return {
        "engagement": engagement,
        "organization": organization,
        "participant_count": len(users),
        "assessments_created": assessments_created,
        "memberships": memberships,
    }
