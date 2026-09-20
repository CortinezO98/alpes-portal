from types import SimpleNamespace

import pytest
from django.core.files.uploadedfile import SimpleUploadedFile
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
    PhaseArtifact,
    ServiceProgram,
)
from apps.programs.services import ensure_participant_phases
from apps.reports.services.pdf_builder import build_individual_report_pdf
from apps.reports.views import _build_dream_tree
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


@pytest.mark.django_db
def test_participant_can_download_own_individual_report_pdf(client, report_setup):
    superadmin, admin, participant, completed = report_setup
    program = ServiceProgram.objects.get(code="jubilacion-plena")
    engagement = Engagement.objects.create(
        title="PDF individual",
        program=program,
        mode=Engagement.Mode.INDIVIDUAL,
        consultant=superadmin,
        status=Engagement.Status.COMPLETED,
    )
    participation = EngagementParticipant.objects.create(
        engagement=engagement,
        participant=participant,
    )
    ensure_participant_phases(participation)

    version = IndividualReportVersion.objects.create(
        engagement_participant=participation,
        version=1,
        executive_summary="Resumen ejecutivo.",
        integral_appreciation="Apreciación integral.",
        recommendations="Recomendaciones.",
        conclusions="Conclusiones.",
        snapshot={
            "participant": {
                "name": participant.email,
                "email": participant.email,
            },
            "engagement": {
                "title": engagement.title,
                "program": program.name,
                "organization": "",
                "consultant": superadmin.email,
            },
            "progress_percent": 100,
            "assessment": None,
            "phases": [],
        },
        created_by=admin,
    )

    client.force_login(participant)
    response = client.get(
        reverse(
            "reports:program-individual-pdf",
            kwargs={"pk": participation.pk, "version": version.version},
        )
    )

    assert response.status_code == 200
    assert response["Content-Type"] == "application/pdf"
    assert response.content.startswith(b"%PDF")
    assert "attachment;" in response["Content-Disposition"]


@pytest.mark.django_db
def test_admin_can_download_organizational_report_pdf(client, report_setup):
    superadmin, admin, participant, _ = report_setup
    program = ServiceProgram.objects.get(code="jubilacion-plena")
    organization = Organization.objects.create(name="Empresa PDF")
    engagement = Engagement.objects.create(
        title="PDF organizacional",
        program=program,
        mode=Engagement.Mode.ORGANIZATIONAL,
        organization=organization,
        consultant=superadmin,
        status=Engagement.Status.COMPLETED,
    )

    version = OrganizationalReportVersion.objects.create(
        engagement=engagement,
        version=1,
        executive_summary="Resumen ejecutivo.",
        organizational_appreciation="Apreciación organizacional.",
        recommendations="Recomendaciones.",
        conclusions="Conclusiones.",
        snapshot={
            "engagement": {
                "title": engagement.title,
                "program": program.name,
                "organization": organization.name,
                "consultant": superadmin.email,
            },
            "participants": {
                "total": 1,
                "completed_assessments": 1,
                "completed_individual_reports": 1,
            },
            "dimension_averages": [
                {"name": "Propósito", "average": 8.5, "participants": 1}
            ],
            "phase_summary": [],
            "privacy_note": "Reporte agregado sin respuestas abiertas identificables.",
        },
        created_by=admin,
    )

    client.force_login(admin)
    response = client.get(
        reverse(
            "reports:program-organizational-pdf",
            kwargs={"pk": engagement.pk, "version": version.version},
        )
    )

    assert response.status_code == 200
    assert response["Content-Type"] == "application/pdf"
    assert response.content.startswith(b"%PDF")
    assert "attachment;" in response["Content-Disposition"]



def test_individual_pdf_renders_complete_roadmap_snapshot():
    report = SimpleNamespace(
        version=3,
        created_at=timezone.now(),
        executive_summary="Resumen con visión integral.",
        integral_appreciation="Apreciación integral del proceso.",
        recommendations="Mantener hábitos y seguimiento.",
        conclusions="La hoja de ruta queda consolidada.",
        snapshot={
            "participant": {
                "name": "Participante Demo",
                "email": "demo@example.com",
            },
            "engagement": {
                "organization": "Empresa Demo",
                "program": "Jubilación Plena",
                "title": "Acompañamiento integral",
                "consultant": "Consultor Demo",
            },
            "progress_percent": 100,
            "assessment": {
                "report": {
                    "dimensions": [
                        {
                            "name": "Propósito",
                            "average": 8.5,
                            "band_label": "Verde",
                            "appreciation": {
                                "interpretation": "Fortaleza consolidada."
                            },
                        }
                    ]
                }
            },
            "phases": [
                {
                    "code": "charla-inicial",
                    "name": "Charla y experiencia del consultor",
                    "status_label": "Completada",
                    "started_at": "2026-09-01T09:00:00",
                    "completed_at": "2026-09-01T10:00:00",
                    "consultant_experience": {
                        "date": "2026-09-01",
                        "topic": "Nueva etapa",
                        "consultant_experience": "Experiencia compartida.",
                        "participant_learnings": "Aprendizajes identificados.",
                        "commitments": "Compromiso personal.",
                        "consultant_appreciation": "Participación activa.",
                    },
                    "sessions": [],
                    "nodes": [],
                    "goals": [],
                    "comments": [
                        {
                            "author": "Consultor Demo",
                            "body": "Buena disposición al proceso.",
                        }
                    ],
                    "artifacts": [
                        {
                            "name": "charla.pdf",
                            "description": "Soporte de la sesión",
                        }
                    ],
                },
                {
                    "code": "conversaciones",
                    "name": "Conversaciones transformadoras",
                    "status_label": "Completada",
                    "started_at": "2026-09-02T09:00:00",
                    "completed_at": "2026-09-02T10:00:00",
                    "sessions": [
                        {
                            "title": "Adaptación al cambio",
                            "date": "2026-09-02",
                            "topics": "Propósito y transición",
                            "findings": "Nuevas prioridades.",
                            "commitments": "Definir acciones.",
                            "consultant_appreciation": "Avance positivo.",
                        }
                    ],
                    "nodes": [],
                    "goals": [],
                    "comments": [],
                    "artifacts": [],
                },
                {
                    "code": "mapa-retos-suenos",
                    "name": "Mapa de retos y sueños",
                    "status_label": "Completada",
                    "started_at": "2026-09-03T09:00:00",
                    "completed_at": "2026-09-03T10:00:00",
                    "sessions": [],
                    "nodes": [
                        {
                            "id": 1,
                            "parent_id": None,
                            "type": "DREAM",
                            "type_label": "Sueño",
                            "title": "Viajar",
                            "description": "Conocer nuevos destinos",
                            "priority_label": "Alta",
                        },
                        {
                            "id": 2,
                            "parent_id": 1,
                            "type": "CHALLENGE",
                            "type_label": "Reto",
                            "title": "Organizar las finanzas",
                            "description": "Preparar el presupuesto",
                            "priority_label": "Alta",
                        },
                        {
                            "id": 3,
                            "parent_id": 2,
                            "type": "GOAL",
                            "type_label": "Meta",
                            "title": "Crear fondo de viajes",
                            "description": "Ahorrar mensualmente",
                            "priority_label": "Alta",
                        },
                        {
                            "id": 4,
                            "parent_id": None,
                            "type": "DREAM",
                            "type_label": "Sueño",
                            "title": "Mantenerme activo",
                            "description": "Construir una nueva rutina.",
                            "priority_label": "Media",
                        },
                        {
                            "id": 5,
                            "parent_id": 4,
                            "type": "MILESTONE",
                            "type_label": "Hito",
                            "title": "Iniciar voluntariado",
                            "description": "Participar en una organización.",
                            "priority_label": "Media",
                        },
                    ],
                    "goals": [],
                    "comments": [],
                    "artifacts": [],
                },
                {
                    "code": "plan-accion",
                    "name": "Plan de acción",
                    "status_label": "Completada",
                    "started_at": "2026-09-04T09:00:00",
                    "completed_at": "2026-09-04T10:00:00",
                    "sessions": [],
                    "nodes": [],
                    "goals": [
                        {
                            "title": "Estabilidad financiera",
                            "description": "Crear un fondo de retiro.",
                            "items": [
                                {
                                    "action": "Crear presupuesto mensual",
                                    "status_label": "En progreso",
                                    "indicator": "Presupuesto documentado",
                                }
                            ],
                        }
                    ],
                    "comments": [],
                    "artifacts": [],
                },
                {
                    "code": "reporte-individual",
                    "name": "Reporte individual",
                    "status_label": "Completada",
                },
            ],
        },
    )

    pdf = build_individual_report_pdf(report)

    assert pdf.startswith(b"%PDF")
    assert len(pdf) > 1000



def test_build_dream_tree_preserves_parent_child_hierarchy():
    tree = _build_dream_tree(
        [
            {"id": 1, "parent_id": None, "title": "Viajar"},
            {"id": 2, "parent_id": 1, "title": "Organizar finanzas"},
            {"id": 3, "parent_id": 2, "title": "Crear fondo"},
            {"id": 4, "parent_id": 3, "title": "Primer viaje"},
        ]
    )

    assert len(tree) == 1
    assert tree[0]["title"] == "Viajar"
    assert tree[0]["children"][0]["title"] == "Organizar finanzas"
    assert tree[0]["children"][0]["children"][0]["title"] == "Crear fondo"
    assert (
        tree[0]["children"][0]["children"][0]["children"][0]["title"]
        == "Primer viaje"
    )



@pytest.mark.django_db
def test_report_view_exposes_existing_phase_support_link(client, report_setup):
    superadmin, admin, participant, _ = report_setup
    program = ServiceProgram.objects.get(code="jubilacion-plena")
    engagement = Engagement.objects.create(
        title="Reporte con soporte",
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
    phase = participation.phase_progress.get(phase__code="charla-inicial")
    artifact = PhaseArtifact.objects.create(
        participant_phase=phase,
        file=SimpleUploadedFile(
            "evidencia.pdf",
            b"%PDF-1.4 evidencia",
            content_type="application/pdf",
        ),
        original_name="evidencia.pdf",
        content_type="application/pdf",
        size_bytes=18,
        uploaded_by=admin,
    )
    version = IndividualReportVersion.objects.create(
        engagement_participant=participation,
        version=1,
        executive_summary="Resumen.",
        integral_appreciation="Apreciación.",
        recommendations="Recomendaciones.",
        conclusions="Conclusiones.",
        snapshot={
            "participant": {"name": participant.email, "email": participant.email},
            "engagement": {
                "title": engagement.title,
                "program": program.name,
                "organization": "",
                "consultant": superadmin.email,
            },
            "progress_percent": 50,
            "assessment": None,
            "phases": [
                {
                    "code": "charla-inicial",
                    "name": "Charla",
                    "order": 1,
                    "status_label": "Completada",
                    "artifacts": [
                        {
                            "name": "evidencia.pdf",
                            "description": "Soporte de prueba",
                            "size_bytes": 18,
                        }
                    ],
                }
            ],
        },
        created_by=admin,
    )

    client.force_login(admin)
    response = client.get(
        reverse("reports:program-individual", kwargs={"pk": participation.pk}),
        {"version": version.version},
    )
    assert response.status_code == 200
    assert b"Abrir soporte" in response.content
    assert reverse(
        "programs:phase-artifact-download",
        kwargs={"pk": artifact.pk},
    ).encode() in response.content

    download = client.get(
        reverse("programs:phase-artifact-download", kwargs={"pk": artifact.pk})
    )
    assert download.status_code == 200
    assert download["Content-Type"] == "application/pdf"


@pytest.mark.django_db
def test_participant_can_open_own_phase_support(client, report_setup):
    superadmin, admin, participant, _ = report_setup
    program = ServiceProgram.objects.get(code="jubilacion-plena")
    engagement = Engagement.objects.create(
        title="Soporte participante",
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
    phase = participation.phase_progress.get(phase__code="charla-inicial")
    artifact = PhaseArtifact.objects.create(
        participant_phase=phase,
        file=SimpleUploadedFile(
            "propio.pdf",
            b"%PDF-1.4 propio",
            content_type="application/pdf",
        ),
        original_name="propio.pdf",
        content_type="application/pdf",
        size_bytes=15,
        uploaded_by=admin,
    )

    client.force_login(participant)
    response = client.get(
        reverse("programs:phase-artifact-download", kwargs={"pk": artifact.pk})
    )
    assert response.status_code == 200
