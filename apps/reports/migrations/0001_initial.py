from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ("assessments", "0007_assessment_engagement_participant"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="DimensionAppreciation",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("interpretation", models.TextField(blank=True)),
                ("strengths", models.TextField(blank=True)),
                ("opportunities", models.TextField(blank=True)),
                ("recommendation", models.TextField(blank=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                (
                    "assessment",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="dimension_appreciations",
                        to="assessments.assessment",
                    ),
                ),
                (
                    "consultant",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="dimension_appreciations",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
                (
                    "dimension",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="report_appreciations",
                        to="assessments.dimension",
                    ),
                ),
            ],
            options={
                "verbose_name": "apreciación por dimensión",
                "verbose_name_plural": "apreciaciones por dimensión",
                "ordering": ("dimension__order", "dimension__id"),
            },
        ),
        migrations.AddConstraint(
            model_name="dimensionappreciation",
            constraint=models.UniqueConstraint(
                fields=("assessment", "dimension"),
                name="report_dimension_appreciation_uniq",
            ),
        ),
    ]
