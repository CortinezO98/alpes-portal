from django.db import migrations, models
import django.db.models.deletion
from django.db.models import Q
from django.utils import timezone


def mark_existing_templates_published(apps, schema_editor):
    AssessmentTemplate = apps.get_model("assessments", "AssessmentTemplate")
    AssessmentTemplate.objects.update(
        publication_status="PUBLISHED",
        version=1,
        published_at=timezone.now(),
    )


class Migration(migrations.Migration):
    dependencies = [
        ("assessments", "0002_question_template_level_support"),
    ]

    operations = [
        migrations.AddField(
            model_name="assessmenttemplate",
            name="version",
            field=models.PositiveSmallIntegerField(default=1),
        ),
        migrations.AddField(
            model_name="assessmenttemplate",
            name="publication_status",
            field=models.CharField(
                choices=[
                    ("DRAFT", "Borrador"),
                    ("PUBLISHED", "Publicada"),
                    ("RETIRED", "Retirada"),
                ],
                db_index=True,
                default="DRAFT",
                max_length=12,
            ),
        ),
        migrations.AddField(
            model_name="assessmenttemplate",
            name="published_at",
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="assessmenttemplate",
            name="supersedes",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.PROTECT,
                related_name="successor_versions",
                to="assessments.assessmenttemplate",
            ),
        ),
        migrations.RunPython(mark_existing_templates_published, migrations.RunPython.noop),
        migrations.AddConstraint(
            model_name="assessmenttemplate",
            constraint=models.UniqueConstraint(
                fields=("supersedes", "version"),
                condition=Q(supersedes__isnull=False),
                name="assess_tpl_supersedes_version_uniq",
            ),
        ),
        migrations.AlterModelOptions(
            name="assessmenttemplate",
            options={
                "ordering": ("name", "-version"),
                "verbose_name": "plantilla de evaluación",
                "verbose_name_plural": "plantillas de evaluación",
            },
        ),
    ]
