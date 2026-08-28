import pytest
from django.core.management import call_command
from django.urls import reverse

from apps.accounts.models import User
from apps.assessments.models import Answer, Assessment, AssessmentTemplate


@pytest.fixture
def assessment_setup(db):
    call_command("seed_jubilacion_plena")
    template = AssessmentTemplate.objects.get(slug="alpes-jubilacion-plena")
    superadmin = User.objects.create_superuser(
        email="superadmin@example.com",
        password="SecurePass123!",
    )
    participant = User.objects.create_user(
        email="participant@example.com",
        password="SecurePass123!",
        role=User.Role.USER,
    )
    assessment = Assessment.objects.create(
        template=template,
        participant=participant,
        created_by=superadmin,
    )
    return superadmin, participant, assessment


@pytest.mark.django_db
def test_superadmin_can_open_assessment_management(client, assessment_setup):
    superadmin, _, _ = assessment_setup
    client.force_login(superadmin)

    response = client.get(reverse("assessments:management-list"))

    assert response.status_code == 200


@pytest.mark.django_db
def test_regular_user_cannot_open_assessment_management(client, assessment_setup):
    _, participant, _ = assessment_setup
    client.force_login(participant)

    response = client.get(reverse("assessments:management-list"))

    assert response.status_code == 403


@pytest.mark.django_db
def test_participant_only_sees_own_assessments(client, assessment_setup):
    superadmin, participant, assessment = assessment_setup
    other = User.objects.create_user(
        email="other@example.com",
        password="SecurePass123!",
        role=User.Role.USER,
    )
    Assessment.objects.create(
        template=assessment.template,
        participant=other,
        created_by=superadmin,
    )
    client.force_login(participant)

    response = client.get(reverse("assessments:my-list"))

    assert response.status_code == 200
    assert list(response.context["assessments"]) == [assessment]


@pytest.mark.django_db
def test_participant_cannot_access_another_users_dimension(client, assessment_setup):
    superadmin, participant, assessment = assessment_setup
    other = User.objects.create_user(
        email="other@example.com",
        password="SecurePass123!",
        role=User.Role.USER,
    )
    other_assessment = Assessment.objects.create(
        template=assessment.template,
        participant=other,
        created_by=superadmin,
    )
    dimension = assessment.template.dimensions.first()
    client.force_login(participant)

    response = client.get(
        reverse(
            "assessments:dimension",
            kwargs={"pk": other_assessment.pk, "dimension_pk": dimension.pk},
        )
    )

    assert response.status_code == 404


@pytest.mark.django_db
def test_dimension_submission_saves_scores_and_marks_progress(client, assessment_setup):
    _, participant, assessment = assessment_setup
    dimension = assessment.template.dimensions.first()
    questions = list(dimension.questions.order_by("order"))
    payload = {f"question_{question.pk}": "8" for question in questions}
    client.force_login(participant)

    response = client.post(
        reverse(
            "assessments:dimension",
            kwargs={"pk": assessment.pk, "dimension_pk": dimension.pk},
        ),
        payload,
    )

    assessment.refresh_from_db()
    assert response.status_code == 302
    assert assessment.status == Assessment.Status.IN_PROGRESS
    assert assessment.started_at is not None
    assert Answer.objects.filter(
        assessment=assessment,
        question__dimension=dimension,
        score=8,
    ).count() == 4


@pytest.mark.django_db
def test_completed_result_exposes_radar_labels_and_scores(client, assessment_setup):
    _, participant, assessment = assessment_setup
    questions = assessment.template.dimensions.order_by("order").values_list(
        "questions__id",
        flat=True,
    )
    for question_id in questions:
        Answer.objects.create(
            assessment=assessment,
            question_id=question_id,
            score=7,
        )
    assessment.status = Assessment.Status.COMPLETED
    assessment.save(update_fields=("status", "updated_at"))
    client.force_login(participant)

    response = client.get(reverse("assessments:result", kwargs={"pk": assessment.pk}))

    assert response.status_code == 200
    assert len(response.context["radar_labels"]) == 8
    assert response.context["radar_scores"] == [7.0] * 8
