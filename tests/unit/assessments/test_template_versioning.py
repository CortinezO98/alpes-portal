import pytest

from apps.assessments.models import AssessmentTemplate, Dimension, Question
from apps.assessments.services.template_versioning import (
    create_next_template_version,
    publish_template,
)


@pytest.mark.django_db
def test_create_next_template_version_clones_structure_without_mutating_source():
    template = AssessmentTemplate.objects.create(
        name="Evaluación dinámica",
        slug="evaluacion-dinamica",
    )
    dimension = Dimension.objects.create(
        template=template,
        name="Dimensión uno",
        slug="dimension-uno",
        order=1,
    )
    Question.objects.create(
        dimension=dimension,
        text="Pregunta original",
        question_type=Question.Type.SCALE,
        order=1,
    )
    Question.objects.create(
        template=template,
        text="Pregunta abierta original",
        question_type=Question.Type.TEXT,
        order=1,
        is_required=False,
    )
    publish_template(template)

    new_template = create_next_template_version(template)

    template.refresh_from_db()
    assert template.publication_status == AssessmentTemplate.PublicationStatus.RETIRED
    assert new_template.version == 2
    assert new_template.publication_status == AssessmentTemplate.PublicationStatus.DRAFT
    assert new_template.supersedes == template
    assert new_template.dimensions.count() == 1
    assert new_template.dimensions.get().questions.get().text == "Pregunta original"
    assert new_template.general_questions.get().text == "Pregunta abierta original"

    cloned_question = new_template.dimensions.get().questions.get()
    cloned_question.text = "Pregunta modificada en v2"
    cloned_question.save(update_fields=("text",))

    assert template.dimensions.get().questions.get().text == "Pregunta original"
