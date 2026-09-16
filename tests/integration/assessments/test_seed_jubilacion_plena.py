import pytest
from django.core.management import call_command

from apps.assessments.models import AssessmentTemplate, Question


@pytest.mark.django_db
def test_seed_jubilacion_plena_creates_canonical_structure():
    call_command("seed_jubilacion_plena")

    template = AssessmentTemplate.objects.get(slug="alpes-jubilacion-plena")

    assert template.name == "ALPES - Jubilación Plena"
    assert template.publication_status == AssessmentTemplate.PublicationStatus.PUBLISHED
    assert template.version == 1
    assert template.published_at is not None
    assert template.dimensions.count() == 8
    assert Question.objects.filter(
        dimension__template=template,
        question_type=Question.Type.SCALE,
    ).count() == 32
    assert template.general_questions.filter(
        question_type=Question.Type.TEXT,
    ).count() == 3


@pytest.mark.django_db
def test_seed_jubilacion_plena_is_idempotent():
    call_command("seed_jubilacion_plena")
    call_command("seed_jubilacion_plena")

    template = AssessmentTemplate.objects.get(slug="alpes-jubilacion-plena")

    assert AssessmentTemplate.objects.filter(slug="alpes-jubilacion-plena").count() == 1
    assert template.dimensions.count() == 8
    assert Question.objects.filter(dimension__template=template).count() == 32
    assert template.general_questions.count() == 3


@pytest.mark.django_db
def test_seed_preserves_source_question_text():
    call_command("seed_jubilacion_plena")

    template = AssessmentTemplate.objects.get(slug="alpes-jubilacion-plena")
    purpose = template.dimensions.get(slug="proposito-motivacion")
    community = template.dimensions.get(slug="contribucion-comunidad")

    assert purpose.questions.get(order=1).text == (
        "Tengo claro cual es mi propósito principal en esta nueva etapa de mi vida."
    )
    assert community.questions.get(order=4).text == (
        "Estoy dispuesto(a) a dedicar tiempo y energia a causas que me importen."
    )
    assert template.general_questions.get(order=3).text == (
        "¿Que esperas encontar en este programa para disfrutar con plenitud esta nueva etapa de tu vida?"
    )
