from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ("programs", "0003_specialized_retirement_phases"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="ConsultantExperienceRecord",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("session_date", models.DateField()),
                ("topic", models.CharField(max_length=180)),
                ("consultant_experience", models.TextField(blank=True)),
                ("participant_learnings", models.TextField(blank=True)),
                ("commitments", models.TextField(blank=True)),
                ("consultant_appreciation", models.TextField(blank=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                (
                    "created_by",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="created_consultant_experiences",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
                (
                    "updated_by",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="updated_consultant_experiences",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
                (
                    "participant_phase",
                    models.OneToOneField(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="consultant_experience",
                        to="programs.participantphase",
                    ),
                ),
            ],
            options={
                "verbose_name": "registro de charla y experiencia",
                "verbose_name_plural": "registros de charla y experiencia",
            },
        ),
    ]
