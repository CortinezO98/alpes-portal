from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ("reports", "0001_initial"),
        ("programs", "0003_specialized_retirement_phases"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="IndividualReportVersion",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("version", models.PositiveSmallIntegerField()),
                ("executive_summary", models.TextField(blank=True)),
                ("integral_appreciation", models.TextField(blank=True)),
                ("recommendations", models.TextField(blank=True)),
                ("conclusions", models.TextField(blank=True)),
                ("snapshot", models.JSONField(default=dict)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                (
                    "created_by",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="created_individual_report_versions",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
                (
                    "engagement_participant",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="individual_report_versions",
                        to="programs.engagementparticipant",
                    ),
                ),
            ],
            options={
                "verbose_name": "versión de reporte individual",
                "verbose_name_plural": "versiones de reporte individual",
                "ordering": ("-version",),
            },
        ),
        migrations.CreateModel(
            name="OrganizationalReportVersion",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("version", models.PositiveSmallIntegerField()),
                ("executive_summary", models.TextField(blank=True)),
                ("organizational_appreciation", models.TextField(blank=True)),
                ("recommendations", models.TextField(blank=True)),
                ("conclusions", models.TextField(blank=True)),
                ("snapshot", models.JSONField(default=dict)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                (
                    "created_by",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="created_organizational_report_versions",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
                (
                    "engagement",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="organizational_report_versions",
                        to="programs.engagement",
                    ),
                ),
            ],
            options={
                "verbose_name": "versión de reporte organizacional",
                "verbose_name_plural": "versiones de reporte organizacional",
                "ordering": ("-version",),
            },
        ),
        migrations.AddConstraint(
            model_name="individualreportversion",
            constraint=models.UniqueConstraint(
                fields=("engagement_participant", "version"),
                name="individual_report_version_uniq",
            ),
        ),
        migrations.AddConstraint(
            model_name="organizationalreportversion",
            constraint=models.UniqueConstraint(
                fields=("engagement", "version"),
                name="organizational_report_version_uniq",
            ),
        ),
    ]
