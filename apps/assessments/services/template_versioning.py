from django.db import transaction
from django.utils import timezone

from apps.assessments.models import AssessmentTemplate, Dimension, Question


@transaction.atomic
def publish_template(template: AssessmentTemplate) -> AssessmentTemplate:
    if template.publication_status != AssessmentTemplate.PublicationStatus.DRAFT:
        return template

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
    """Clone a template into a draft without changing the currently published version."""
    next_version = template.version + 1
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
