from django.db import migrations, models
from django.db.models import Q
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [
        ("assessments", "0001_initial"),
    ]

    operations = [
        migrations.AlterField(
            model_name="question",
            name="dimension",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                related_name="questions",
                to="assessments.dimension",
            ),
        ),
        migrations.AddField(
            model_name="question",
            name="template",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                related_name="general_questions",
                to="assessments.assessmenttemplate",
            ),
        ),
        migrations.AlterModelOptions(
            name="question",
            options={
                "ordering": ("order", "id"),
                "verbose_name": "pregunta",
                "verbose_name_plural": "preguntas",
            },
        ),
        migrations.AddConstraint(
            model_name="question",
            constraint=models.UniqueConstraint(
                condition=Q(dimension__isnull=True),
                fields=("template", "order"),
                name="assess_tpl_order_uniq",
            ),
        ),
        migrations.AddConstraint(
            model_name="question",
            constraint=models.CheckConstraint(
                condition=(
                    Q(dimension__isnull=False, template__isnull=True)
                    | Q(dimension__isnull=True, template__isnull=False)
                ),
                name="assess_question_parent_xor",
            ),
        ),
        migrations.AddConstraint(
            model_name="question",
            constraint=models.CheckConstraint(
                condition=(Q(question_type="TEXT") | Q(dimension__isnull=False)),
                name="assess_scale_needs_dim",
            ),
        ),
    ]
