from django.db import migrations


OPEN_QUESTIONS = (
    "¿Que sueños o metas te gustaría alcanzar durante esta etapa de tu vida?",
    "¿Hay algo más que te gustaría compartir sobre tus expectativas o preocupaciones respecto a la jubilación?",
    "¿Que esperas encontar en este programa para disfrutar con plenitud esta nueva etapa de tu vida?",
)


def ensure_open_questions(apps, schema_editor):
    AssessmentTemplate = apps.get_model("assessments", "AssessmentTemplate")
    Question = apps.get_model("assessments", "Question")

    template = AssessmentTemplate.objects.filter(slug="alpes-jubilacion-plena").first()
    if template is None:
        return

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
        ("assessments", "0004_seed_jubilacion_plena"),
    ]

    operations = [
        migrations.RunPython(ensure_open_questions, migrations.RunPython.noop),
    ]
