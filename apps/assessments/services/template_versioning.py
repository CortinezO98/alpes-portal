from django.core.exceptions import ValidationError
from django.db import transaction
from django.utils import timezone

from apps.assessments.models import AssessmentTemplate, Dimension, Question


def validate_template_ready(template: AssessmentTemplate) -> None:
    dimensions = list(template.dimensions.prefetch_related("questions").order_by("order", "id"))
    if not dimensions:
        raise ValidationError("La plantilla debe tener al menos una dimensión antes de publicarse.")

    empty_dimensions = [
        dimension.name
        for dimension in dimensions
        if not dimension.questions.filter(question_type=Question.Type.SCALE).exists()
    ]
    if empty_dimensions:
        names = ", ".join(empty_dimensions)
        raise ValidationError(
            f"Cada dimensión debe tener al menos una pregunta de escala. Revisa: {names}."
        )


@transaction.atomic
def publish_template(template: AssessmentTemplate) -> AssessmentTemplate:
    if template.publication_status != AssessmentTemplate.PublicationStatus.DRAFT:
        return template

    validate_template_ready(template)

    if template.supersedes_id:
        previous = template.supersedes
        if previous.publication_status == AssessmentTemplate.PublicationStatus.PUBLISHED:
            previous.publication_status = AssessmentTemplate.PublicationStatus.RETIRED
            previous.is_active = False
            previous.save(update_fields=("publication_status", "is_active", "updated_at"))

    template.publication_status = AssessmentTemplate.PublicationStatus.PUBLISHED
    template.published_at = timezone.now()
    template.is_active = True
    template.save(
        update_fields=("publication_status", "published_at", "is_active", "updated_at")
    )
    return template


@transaction.atomic
def create_next_template_version(template: AssessmentTemplate) -> AssessmentTemplate:
    """Clone a published template into a draft without changing the active version."""
    if template.publication_status != AssessmentTemplate.PublicationStatus.PUBLISHED:
        raise ValidationError("Solo una plantilla publicada puede originar una nueva versión.")

    next_version = template.version + 1
    existing = template.successor_versions.filter(version=next_version).first()
    if existing:
        return existing

    base_slug = template.slug.rsplit("-v", 1)[0]
    new_template = AssessmentTemplate.objects.create(
        name=template.name,
        slug=f"{base_slug}-v{next_version}",
        description=template.description,
        version=next_version,
        publication_status=AssessmentTemplate.PublicationStatus.DRAFT,
        supersedes=template,
        is_active=False,
    )

    for dimension in template.dimensions.prefetch_related("questions").order_by("order", "id"):
        cloned_dimension = Dimension.objects.create(
            template=new_template,
            name=dimension.name,
            slug=dimension.slug,
            description=dimension.description,
            order=dimension.order,
        )
        Question.objects.bulk_create(
            [
                Question(
                    dimension=cloned_dimension,
                    text=question.text,
                    question_type=question.question_type,
                    order=question.order,
                    is_required=question.is_required,
                )
                for question in dimension.questions.all()
            ]
        )

    Question.objects.bulk_create(
        [
            Question(
                template=new_template,
                text=question.text,
                question_type=question.question_type,
                order=question.order,
                is_required=question.is_required,
            )
            for question in template.general_questions.order_by("order", "id")
        ]
    )
    return new_template
