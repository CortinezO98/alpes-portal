import pytest
from django.core.management import call_command
from django.urls import reverse
from django.utils import timezone

from apps.accounts.models import User
from apps.assessments.models import Answer, Assessment, AssessmentTemplate, Question
from apps.programs.models import (
    Engagement,
    EngagementParticipant,
    Organization,
    ParticipantPhase,
    ServiceProgram,
)
from apps.programs.services import ensure_participant_phases
from apps.reports.models import (
    DimensionAppreciation,
    IndividualReportVersion,
    OrganizationalReportVersion,
)


@pytest.fixture
def report_setup(db):
    call_command("seed_jubilacion_plena")
    template = AssessmentTemplate.objects.get(slug="alpes-jubilacion-plena")
    superadmin = User.objects.create_superuser(
        email="superadmin@example.com",
        password="SecurePass123!",
    )
    admin = User.objects.create_user(
        email="admin@example.com",
        password="SecurePass123!",
        role=User.Role.ADMIN,
        is_staff=True,
    )
    participant = User.objects.create_user(
        email="participant@example.com",
        password="SecurePass123!",
        role=User.Role.USER,
    )
    completed = Assessment.objects.create(
        template=template,
        participant=participant,
        created_by=superadmin,
        status=Assessment.Status.COMPLETED,
        started_at=timezone.now(),
        completed_at=timezone.now(),
    )
    for question in Question.objects.filter(
        dimension__template=template,
        question_type=Question.Type.SCALE,
    ):
        Answer.objects.create(
            assessment=completed,
            question=question,
            score=8,
        )
    Assessment.objects.create(
        template=template,
        participant=participant,
        created_by=admin,
        status=Assessment.Status.IN_PROGRESS,
        started_at=timezone.now(),
    )
    return superadmin, admin, participant, completed


@pytest.mark.django_db
def test_admin_can_access_analytics_dashboard(client, report_setup):
    _, admin, _, _ = report_setup
    client.force_login(admin)

    response = client.get(reverse("reports:dashboard"))

    assert response.status_code == 200
    assert response.context["total_assessments"] == 2
    assert response.context["completed_count"] == 1
    assert response.context["in_progress_count"] == 1
    assert response.context["completion_rate"] == 50


@pytest.mark.django_db
def test_regular_user_cannot_access_analytics_dashboard(client, report_setup):
    _, _, participant, _ = report_setup
    client.force_login(participant)

    response = client.get(reverse("reports:dashboard"))

    assert response.status_code == 403


@pytest.mark.django_db
def test_analytics_status_filter_limits_metrics(client, report_setup):
    superadmin, _, _, _ = report_setup
    client.force_login(superadmin)

    response = client.get(
        reverse("reports:dashboard"),
        {"status": Assessment.Status.COMPLETED},
    )

    assert response.status_code == 200
    assert response.context["total_assessments"] == 1
    assert response.context["completed_count"] == 1
    assert response.context["in_progress_count"] == 0
    assert response.context["completion_rate"] == 100


@pytest.mark.django_db
def test_admin_can_open_dynamic_individual_assessment_report(client, report_setup):
    _, admin, _, completed = report_setup
    client.force_login(admin)

    response = client.get(
        reverse("reports:assessment-detail", kwargs={"pk": completed.pk})
    )

    assert response.status_code == 200
    assert response.context["assessment"] == completed
    assert len(response.context["report_dimensions"]) == 8
    assert len(response.context["radar_dimensions"]) == 8
    assert all(item["score"] == 8.0 for item in response.context["radar_dimensions"])
    assert all(item["band"] == "green" for item in response.context["radar_dimensions"])
    assert all(item["band_label"] == "Verde" for item in response.context["radar_dimensions"])
    assert all(len(item["questions"]) == 4 for item in response.context["report_dimensions"])


@pytest.mark.django_db
def test_report_semaforizes_dimension_and_questions_from_database(client, report_setup):
    _, admin, _, completed = report_setup
    first_dimension = completed.template.dimensions.order_by("order", "id").first()
    answers = list(
        Answer.objects.filter(
            assessment=completed,
            question__dimension=first_dimension,
        ).order_by("question__order", "question__id")
    )
    for answer, score in zip(answers, (5, 6, 8, 10), strict=True):
        answer.score = score
        answer.save(update_fields=("score", "updated_at"))

    client.force_login(admin)
    response = client.get(
        reverse("reports:assessment-detail", kwargs={"pk": completed.pk})
    )

    dimension = response.context["report_dimensions"][0]
    radar_dimension = response.context["radar_dimensions"][0]
    assert dimension["average"] == 7.25
    assert dimension["band"] == "yellow"
    assert dimension["band_label"] == "Amarillo"
    assert radar_dimension["band_label"] == "Amarillo"
    assert [item["band"] for item in dimension["questions"]] == [
        "red",
        "yellow",
        "green",
        "green",
    ]
    assert [item["band_label"] for item in dimension["questions"]] == [
        "Rojo",
        "Amarillo",
        "Verde",
        "Verde",
    ]


@pytest.mark.django_db
def test_qualitative_answers_are_preserved_but_not_rendered_in_results(client, report_setup):
    _, admin, _, completed = report_setup
    open_question = Question.objects.filter(
        template=completed.template,
        dimension__isnull=True,
        question_type=Question.Type.TEXT,
    ).order_by("order", "id").first()
    assert open_question is not None

    Answer.objects.create(
        assessment=completed,
        question=open_question,
        text="Libertad financiera",
    )

    client.force_login(admin)
    response = client.get(
        reverse("reports:assessment-detail", kwargs={"pk": completed.pk})
    )

    assert response.status_code == 200
    assert response.context["general_answers"][0]["answer"] == "Libertad financiera"
    assert b"Lectura cualitativa" not in response.content
    assert b"Libertad financiera" not in response.content


@pytest.mark.django_db
def test_admin_can_save_dimension_appreciation(client, report_setup):
    _, admin, _, completed = report_setup
    dimension = completed.template.dimensions.order_by("order", "id").first()
    client.force_login(admin)

    response = client.post(
        reverse(
            "reports:dimension-appreciation",
            kwargs={
                "assessment_pk": completed.pk,
                "dimension_pk": dimension.pk,
            },
        ),
        {
            "interpretation": "Lectura profesional de prueba.",
            "strengths": "Fortaleza observada.",
            "opportunities": "Oportunidad prioritaria.",
            "recommendation": "Acción recomendada.",
        },
    )

    assert response.status_code == 302
    appreciation = DimensionAppreciation.objects.get(
        assessment=completed,
        dimension=dimension,
    )
    assert appreciation.consultant == admin
    assert appreciation.interpretation == "Lectura profesional de prueba."

    detail = client.get(
        reverse("reports:assessment-detail", kwargs={"pk": completed.pk})
    )
    first_dimension = detail.context["report_dimensions"][0]
    assert first_dimension["appreciation"]["recommendation"] == "Acción recomendada."



@pytest.mark.django_db
def test_admin_generates_versioned_individual_program_report(client, report_setup):
    superadmin, admin, participant, completed = report_setup
    program = ServiceProgram.objects.get(code="jubilacion-plena")
    engagement = Engagement.objects.create(
        title="Jubilación integral",
        program=program,
        mode=Engagement.Mode.INDIVIDUAL,
        consultant=superadmin,
        status=Engagement.Status.ACTIVE,
    )
    participation = EngagementParticipant.objects.create(
        engagement=engagement,
        participant=participant,
    )
    ensure_participant_phases(participation)
    completed.engagement_participant = participation
    completed.save(update_fields=("engagement_participant", "updated_at"))

    report_progress = participation.phase_progress.get(
        phase__code="reporte-individual"
    )
    participation.phase_progress.filter(
        phase__order__lt=report_progress.phase.order
    ).update(status=ParticipantPhase.Status.COMPLETED)

    for dimension in completed.template.dimensions.all():
        DimensionAppreciation.objects.create(
            assessment=completed,
            dimension=dimension,
            consultant=admin,
            interpretation=f"Lectura {dimension.name}",
            strengths="Fortaleza",
            opportunities="Oportunidad",
            recommendation="Recomendación",
        )

    client.force_login(admin)
    response = client.post(
        reverse(
            "reports:program-individual-generate",
            kwargs={"pk": participation.pk},
        ),
        {
            "executive_summary": "Resumen ejecutivo.",
            "integral_appreciation": "Lectura integral.",
            "recommendations": "Recomendaciones.",
            "conclusions": "Conclusiones.",
        },
    )

    assert response.status_code == 302
    version = IndividualReportVersion.objects.get(
        engagement_participant=participation,
        version=1,
    )
    assert version.snapshot["participant"]["email"] == participant.email
    assert version.snapshot["assessment"]["report"]["dimensions"]
    report_progress.refresh_from_db()
    assert report_progress.status == ParticipantPhase.Status.COMPLETED


@pytest.mark.django_db
def test_admin_generates_aggregated_organizational_report(client, report_setup):
    superadmin, admin, participant, completed = report_setup
    program = ServiceProgram.objects.get(code="jubilacion-plena")
    organization = Organization.objects.create(name="Organización Reporte")
    engagement = Engagement.objects.create(
        title="Jubilación organizacional",
        program=program,
        mode=Engagement.Mode.ORGANIZATIONAL,
        organization=organization,
        consultant=superadmin,
        status=Engagement.Status.ACTIVE,
    )
    participation = EngagementParticipant.objects.create(
        engagement=engagement,
        participant=participant,
    )
    ensure_participant_phases(participation)
    completed.engagement_participant = participation
    completed.save(update_fields=("engagement_participant", "updated_at"))
    participation.phase_progress.update(status=ParticipantPhase.Status.COMPLETED)

    client.force_login(admin)
    response = client.post(
        reverse(
            "reports:program-organizational-generate",
            kwargs={"pk": engagement.pk},
        ),
        {
            "executive_summary": "Resumen organización.",
            "organizational_appreciation": "Lectura agregada.",
            "recommendations": "Recomendaciones organizacionales.",
            "conclusions": "Conclusiones organizacionales.",
        },
    )

    assert response.status_code == 302
    version = OrganizationalReportVersion.objects.get(
        engagement=engagement,
        version=1,
    )
    assert version.snapshot["participants"]["total"] == 1
    assert version.snapshot["dimension_averages"]
    assert "general_answers" not in version.snapshot
    engagement.refresh_from_db()
    assert engagement.status == Engagement.Status.COMPLETED
