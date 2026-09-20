from django.db import transaction
from django.utils import timezone

from .models import Engagement, Organization, ParticipantPhase


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
        context_name = (
            organization.name
            if organization is not None
            else "Individual"
        )
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
