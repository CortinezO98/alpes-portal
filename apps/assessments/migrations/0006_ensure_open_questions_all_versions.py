from django.db import migrations


OPEN_QUESTIONS = (
    "¿Qué sueños o metas te gustaría alcanzar durante esta etapa de tu vida?",
    "¿Hay algo más que te gustaría compartir sobre tus expectativas o preocupaciones respecto a la jubilación?",
    "¿Qué esperas encontrar en este programa para disfrutar con plenitud esta nueva etapa de tu vida?",
)


def ensure_open_questions_all_versions(apps, schema_editor):
    AssessmentTemplate = apps.get_model("assessments", "AssessmentTemplate")
    Question = apps.get_model("assessments", "Question")

    templates = AssessmentTemplate.objects.filter(
        slug__startswith="alpes-jubilacion-plena"
    ).order_by("version", "id")

    for template in templates:
        for order, text in enumerate(OPEN_QUESTIONS, start=1):
            Question.objects.update_or_create(
                template=template,
                dimension=None,
                order=order,
                defaults={
                    "text": text,
                    "question_type": "TEXT",
                    "is_required": False,
                },
            )


class Migration(migrations.Migration):
    dependencies = [
        ("assessments", "0005_ensure_jubilacion_open_questions"),
    ]

    operations = [
        migrations.RunPython(
            ensure_open_questions_all_versions,
            migrations.RunPython.noop,
        ),
    ]
