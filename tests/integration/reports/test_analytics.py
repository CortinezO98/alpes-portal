import pytest
from django.core.management import call_command
from django.urls import reverse
from django.utils import timezone

from apps.accounts.models import User
from apps.assessments.models import Answer, Assessment, AssessmentTemplate, Question


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
def test_admin_can_open_individual_assessment_report(client, report_setup):
    _, admin, _, completed = report_setup
    client.force_login(admin)

    response = client.get(
        reverse("reports:assessment-detail", kwargs={"pk": completed.pk})
    )

    assert response.status_code == 200
    assert response.context["assessment"] == completed
    assert len(response.context["radar_labels"]) == 8
    assert response.context["radar_scores"] == [8.0] * 8
