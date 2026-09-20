from django.db import migrations


SOURCE_OPEN_QUESTIONS = (
    "¿Que sueños o metas te gustaría alcanzar durante esta etapa de tu vida?",
    "¿Hay algo más que te gustaría compartir sobre tus expectativas o preocupaciones respecto a la jubilación?",
    "¿Que esperas encontar en este programa para disfrutar con plenitud esta nueva etapa de tu vida?",
)


def restore_source_question_text(apps, schema_editor):
    AssessmentTemplate = apps.get_model("assessments", "AssessmentTemplate")
    Question = apps.get_model("assessments", "Question")

    templates = AssessmentTemplate.objects.filter(
        slug__startswith="alpes-jubilacion-plena"
    )

    for template in templates:
        for order, text in enumerate(SOURCE_OPEN_QUESTIONS, start=1):
            Question.objects.filter(
                template=template,
                dimension__isnull=True,
                order=order,
            ).update(text=text)


class Migration(migrations.Migration):
    dependencies = [
        ("assessments", "0007_assessment_engagement_participant"),
    ]

    operations = [
        migrations.RunPython(
            restore_source_question_text,
            migrations.RunPython.noop,
        ),
    ]
