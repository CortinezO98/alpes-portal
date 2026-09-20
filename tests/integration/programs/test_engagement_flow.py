import pytest
from django.core.management import call_command
from django.urls import reverse
from django.utils import timezone

from apps.accounts.models import User
from apps.assessments.models import Assessment, AssessmentTemplate
from apps.programs.models import (
    Engagement,
    EngagementParticipant,
    EngagementPhase,
    Organization,
    ParticipantPhase,
    ServiceProgram,
)
from apps.programs.services import (
    ensure_participant_phases,
    mark_assessment_phase_completed,
)


@pytest.fixture
def program_setup(db):
    program = ServiceProgram.objects.get(code="jubilacion-plena")
    superadmin = User.objects.create_superuser(
        email="superadmin-programs@example.com",
        password="SecurePass123!",
    )
    participant = User.objects.create_user(
        email="participant-programs@example.com",
        password="SecurePass123!",
        role=User.Role.USER,
    )
    return program, superadmin, participant


@pytest.mark.django_db
def test_individual_engagement_creates_six_participant_phases(program_setup):
    program, superadmin, participant = program_setup
    engagement = Engagement.objects.create(
        title="Jubilación individual",
        program=program,
        mode=Engagement.Mode.INDIVIDUAL,
        consultant=superadmin,
        status=Engagement.Status.ACTIVE,
    )
    membership = EngagementParticipant.objects.create(
        engagement=engagement,
        participant=participant,
    )

    ensure_participant_phases(membership)

    assert membership.phase_progress.count() == 6
    assert not membership.phase_progress.filter(
        phase__code="reporte-organizacional"
    ).exists()


@pytest.mark.django_db
def test_organizational_engagement_creates_process_level_report(program_setup):
    program, superadmin, participant = program_setup
    organization = Organization.objects.create(name="Empresa Demo")
    engagement = Engagement.objects.create(
        title="Jubilación Empresa Demo",
        program=program,
        mode=Engagement.Mode.ORGANIZATIONAL,
        organization=organization,
        consultant=superadmin,
        status=Engagement.Status.ACTIVE,
    )
    membership = EngagementParticipant.objects.create(
        engagement=engagement,
        participant=participant,
    )

    ensure_participant_phases(membership)

    assert membership.phase_progress.count() == 6
    assert not membership.phase_progress.filter(
        phase__code="reporte-organizacional"
    ).exists()
    assert EngagementPhase.objects.filter(
        engagement=engagement,
        phase__code="reporte-organizacional",
    ).exists()


@pytest.mark.django_db
def test_completed_assessment_completes_life_wheel_phase(program_setup):
    program, superadmin, participant = program_setup
    call_command("seed_jubilacion_plena")
    template = AssessmentTemplate.objects.filter(
        slug__startswith="alpes-jubilacion-plena",
        publication_status=AssessmentTemplate.PublicationStatus.PUBLISHED,
    ).order_by("-version").first()

    engagement = Engagement.objects.create(
        title="Seguimiento automático",
        program=program,
        mode=Engagement.Mode.INDIVIDUAL,
        consultant=superadmin,
        status=Engagement.Status.ACTIVE,
    )
    membership = EngagementParticipant.objects.create(
        engagement=engagement,
        participant=participant,
    )
    ensure_participant_phases(membership)

    assessment = Assessment.objects.create(
        template=template,
        participant=participant,
        created_by=superadmin,
        engagement_participant=membership,
        status=Assessment.Status.COMPLETED,
        started_at=timezone.now(),
        completed_at=timezone.now(),
    )

    mark_assessment_phase_completed(assessment, actor=participant)

    progress = membership.phase_progress.get(phase__code="rueda-vida")
    assert progress.status == ParticipantPhase.Status.COMPLETED
    assert progress.completed_at is not None


@pytest.mark.django_db
def test_superadmin_can_open_engagement_list(client, program_setup):
    _, superadmin, _ = program_setup
    client.force_login(superadmin)

    response = client.get(reverse("programs:engagement-list"))

    assert response.status_code == 200


@pytest.mark.django_db
def test_unified_form_creates_company_process_participant_and_assessment(client, program_setup):
    program, superadmin, participant = program_setup
    call_command("seed_jubilacion_plena")
    template = AssessmentTemplate.objects.filter(
        slug__startswith="alpes-jubilacion-plena",
        publication_status=AssessmentTemplate.PublicationStatus.PUBLISHED,
    ).order_by("-version").first()
    client.force_login(superadmin)

    response = client.post(
        reverse("programs:engagement-create"),
        {
            "mode": Engagement.Mode.ORGANIZATIONAL,
            "title": "",
            "program": program.pk,
            "organization": "",
            "create_organization": "on",
            "organization_name": "Empresa Prueba",
            "organization_tax_id": "900999111-1",
            "organization_contact_name": "Contacto Demo",
            "organization_contact_email": "contacto@empresa-prueba.test",
            "participants": [participant.pk],
            "new_participants_json": "[]",
            "status": Engagement.Status.ACTIVE,
            "start_date": "",
            "end_date": "",
            "assign_assessment": "on",
            "assessment_template": template.pk,
            "notes": "",
        },
    )

    engagement = Engagement.objects.get(organization__name="Empresa Prueba")
    membership = engagement.participants.get(participant=participant)

    assert response.status_code == 302
    assert engagement.organization.name == "Empresa Prueba"
    assert engagement.title.startswith("Jubilación Plena · Empresa Prueba ·")
    assert membership.phase_progress.count() == 6
    assert engagement.phase_progress.filter(
        phase__code="reporte-organizacional"
    ).exists()
    assert Assessment.objects.filter(
        participant=participant,
        engagement_participant=membership,
        template=template,
    ).exists()


@pytest.mark.django_db
def test_first_phase_is_available_and_next_unlocks_after_approval(program_setup):
    program, superadmin, participant = program_setup
    engagement = Engagement.objects.create(
        title="Secuencia Jubilación",
        program=program,
        mode=Engagement.Mode.INDIVIDUAL,
        consultant=superadmin,
        status=Engagement.Status.ACTIVE,
    )
    membership = EngagementParticipant.objects.create(
        engagement=engagement,
        participant=participant,
    )
    ensure_participant_phases(membership)

    phases = list(membership.phase_progress.select_related("phase").order_by("phase__order"))
    assert phases[0].status == ParticipantPhase.Status.AVAILABLE
    assert phases[1].status == ParticipantPhase.Status.PENDING

    phases[0].status = ParticipantPhase.Status.SUBMITTED
    phases[0].save(update_fields=("status", "updated_at"))

    from apps.programs.services import review_participant_phase

    review_participant_phase(
        phases[0],
        actor=superadmin,
        approve=True,
        note="Fase validada.",
    )

    phases[1].refresh_from_db()
    assert phases[1].status == ParticipantPhase.Status.AVAILABLE


@pytest.mark.django_db
def test_life_wheel_completion_does_not_skip_locked_previous_phase(program_setup):
    program, superadmin, participant = program_setup
    call_command("seed_jubilacion_plena")
    template = AssessmentTemplate.objects.filter(
        slug__startswith="alpes-jubilacion-plena",
        publication_status=AssessmentTemplate.PublicationStatus.PUBLISHED,
    ).order_by("-version").first()
    engagement = Engagement.objects.create(
        title="Secuencia estricta",
        program=program,
        mode=Engagement.Mode.INDIVIDUAL,
        consultant=superadmin,
        status=Engagement.Status.ACTIVE,
    )
    membership = EngagementParticipant.objects.create(
        engagement=engagement,
        participant=participant,
    )
    ensure_participant_phases(membership)
    assessment = Assessment.objects.create(
        template=template,
        participant=participant,
        created_by=superadmin,
        engagement_participant=membership,
        status=Assessment.Status.COMPLETED,
        started_at=timezone.now(),
        completed_at=timezone.now(),
    )

    mark_assessment_phase_completed(assessment, actor=participant)

    conversation = membership.phase_progress.get(phase__code="conversaciones")
    initial = membership.phase_progress.get(phase__code="charla-inicial")
    assert initial.status == ParticipantPhase.Status.AVAILABLE
    assert conversation.status == ParticipantPhase.Status.PENDING
