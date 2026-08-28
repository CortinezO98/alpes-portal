import pytest
from django.core.exceptions import ValidationError
from django.db import IntegrityError

from apps.accounts.models import User
from apps.assessments.models import (
    Answer,
    Assessment,
    AssessmentTemplate,
    Dimension,
    Question,
)


@pytest.mark.django_db
def test_assessment_domain_can_be_created():
    creator = User.objects.create_superuser(
        email="superadmin@example.com",
        password="SecurePass123!",
    )
    participant = User.objects.create_user(
        email="participant@example.com",
        password="SecurePass123!",
    )
    template = AssessmentTemplate.objects.create(
        name="ALPES Jubilación Plena",
        slug="alpes-jubilacion-plena",
    )
    dimension = Dimension.objects.create(
        template=template,
        name="Propósito y Motivación",
        slug="proposito-motivacion",
        order=1,
    )
    question = Question.objects.create(
        dimension=dimension,
        text="Me siento motivado frente a esta nueva etapa de vida.",
        question_type=Question.Type.SCALE,
        order=1,
    )
    assessment = Assessment.objects.create(
        template=template,
        participant=participant,
        created_by=creator,
    )
    answer = Answer(
        assessment=assessment,
        question=question,
        score=8,
    )
    answer.full_clean()
    answer.save()

    assert assessment.status == Assessment.Status.DRAFT
    assert assessment.answers.get().score == 8


@pytest.mark.django_db
def test_scale_answer_rejects_score_outside_one_to_ten():
    creator = User.objects.create_superuser(
        email="superadmin@example.com",
        password="SecurePass123!",
    )
    participant = User.objects.create_user(
        email="participant@example.com",
        password="SecurePass123!",
    )
    template = AssessmentTemplate.objects.create(
        name="ALPES",
        slug="alpes",
    )
    dimension = Dimension.objects.create(
        template=template,
        name="Bienestar",
        slug="bienestar",
        order=1,
    )
    question = Question.objects.create(
        dimension=dimension,
        text="Valoración de bienestar",
        order=1,
    )
    assessment = Assessment.objects.create(
        template=template,
        participant=participant,
        created_by=creator,
    )
    answer = Answer(
        assessment=assessment,
        question=question,
        score=11,
    )

    with pytest.raises(ValidationError):
        answer.full_clean()


@pytest.mark.django_db
def test_dimension_order_is_unique_per_template():
    template = AssessmentTemplate.objects.create(
        name="ALPES",
        slug="alpes",
    )
    Dimension.objects.create(
        template=template,
        name="Dimensión A",
        slug="dimension-a",
        order=1,
    )

    with pytest.raises(IntegrityError):
        Dimension.objects.create(
            template=template,
            name="Dimensión B",
            slug="dimension-b",
            order=1,
        )


@pytest.mark.django_db
def test_only_one_answer_exists_per_assessment_and_question():
    creator = User.objects.create_superuser(
        email="superadmin@example.com",
        password="SecurePass123!",
    )
    participant = User.objects.create_user(
        email="participant@example.com",
        password="SecurePass123!",
    )
    template = AssessmentTemplate.objects.create(
        name="ALPES",
        slug="alpes",
    )
    dimension = Dimension.objects.create(
        template=template,
        name="Bienestar",
        slug="bienestar",
        order=1,
    )
    question = Question.objects.create(
        dimension=dimension,
        text="Valoración de bienestar",
        order=1,
    )
    assessment = Assessment.objects.create(
        template=template,
        participant=participant,
        created_by=creator,
    )
    Answer.objects.create(
        assessment=assessment,
        question=question,
        score=7,
    )

    with pytest.raises(IntegrityError):
        Answer.objects.create(
            assessment=assessment,
            question=question,
            score=8,
        )
