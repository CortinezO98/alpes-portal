from django.db import transaction
from django.utils import timezone

from apps.assessments.models import AssessmentTemplate, Dimension, Question


def publish_template(template: AssessmentTemplate) -> AssessmentTemplate:
    if template.publication_status != AssessmentTemplate.PublicationStatus.DRAFT:
        return template
    template.publication_status = AssessmentTemplate.PublicationStatus.PUBLISHED
    template.published_at = timezone.now()
    template.save(update_fields=("publication_status", "published_at", "updated_at"))
    return template


@transaction.atomic
def create_next_template_version(template: AssessmentTemplate) -> AssessmentTemplate:
    """Clone a template so published historical versions remain immutable in practice."""
    next_version = template.version + 1
    base_slug = template.slug.rsplit("-v", 1)[0]
    new_template = AssessmentTemplate.objects.create(
        name=template.name,
        slug=f"{base_slug}-v{next_version}",
        description=template.description,
        version=next_version,
        publication_status=AssessmentTemplate.PublicationStatus.DRAFT,
        supersedes=template,
        is_active=True,
    )

    dimension_map = {}
    for dimension in template.dimensions.prefetch_related("questions").order_by("order", "id"):
        cloned_dimension = Dimension.objects.create(
            template=new_template,
            name=dimension.name,
            slug=dimension.slug,
            description=dimension.description,
            order=dimension.order,
        )
        dimension_map[dimension.pk] = cloned_dimension
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

    if template.publication_status == AssessmentTemplate.PublicationStatus.PUBLISHED:
        template.publication_status = AssessmentTemplate.PublicationStatus.RETIRED
        template.is_active = False
        template.save(update_fields=("publication_status", "is_active", "updated_at"))

    return new_template
