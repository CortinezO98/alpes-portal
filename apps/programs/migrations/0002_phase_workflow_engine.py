from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


def configure_phase_engine(apps, schema_editor):
    ProgramPhase = apps.get_model("programs", "ProgramPhase")
    Engagement = apps.get_model("programs", "Engagement")
    EngagementPhase = apps.get_model("programs", "EngagementPhase")
    ParticipantPhase = apps.get_model("programs", "ParticipantPhase")

    participant_codes_requiring_support = {
        "charla-inicial",
        "rueda-vida",
        "conversaciones",
        "mapa-retos-suenos",
        "plan-accion",
    }

    ProgramPhase.objects.filter(code="reporte-organizacional").update(
        scope="ENGAGEMENT",
        participant_visible=False,
        requires_review=True,
        requires_artifact=False,
    )
    ProgramPhase.objects.exclude(code="reporte-organizacional").update(
        scope="PARTICIPANT",
    )
    ProgramPhase.objects.filter(code__in=participant_codes_requiring_support).update(
        allows_artifacts=True,
        requires_artifact=True,
        requires_review=True,
    )
    ProgramPhase.objects.filter(code="reporte-individual").update(
        allows_artifacts=True,
        requires_artifact=False,
        requires_review=True,
    )

    organizational_phase = ProgramPhase.objects.filter(
        code="reporte-organizacional"
    ).first()
    if organizational_phase:
        for engagement in Engagement.objects.filter(mode="ORGANIZATIONAL"):
            EngagementPhase.objects.get_or_create(
                engagement=engagement,
                phase=organizational_phase,
                defaults={"status": "PENDING"},
            )

        ParticipantPhase.objects.filter(
            phase=organizational_phase
        ).delete()

    for engagement in Engagement.objects.all():
        for membership in engagement.participants.all():
            progresses = list(
                ParticipantPhase.objects.filter(
                    engagement_participant=membership,
                    phase__scope="PARTICIPANT",
                ).order_by("phase__order", "id")
            )
            if progresses and not any(
                item.status in {"IN_PROGRESS", "COMPLETED"} for item in progresses
            ):
                first = progresses[0]
                first.status = "AVAILABLE"
                first.save(update_fields=["status"])


class Migration(migrations.Migration):

    dependencies = [
        ("programs", "0001_initial"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.AddField(
            model_name="programphase",
            name="allows_artifacts",
            field=models.BooleanField(default=True),
        ),
        migrations.AddField(
            model_name="programphase",
            name="requires_artifact",
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name="programphase",
            name="requires_review",
            field=models.BooleanField(default=True),
        ),
        migrations.AddField(
            model_name="programphase",
            name="scope",
            field=models.CharField(
                choices=[
                    ("PARTICIPANT", "Participante"),
                    ("ENGAGEMENT", "Proceso / empresa"),
                ],
                default="PARTICIPANT",
                max_length=20,
            ),
        ),
        migrations.AlterField(
            model_name="participantphase",
            name="status",
            field=models.CharField(
                choices=[
                    ("PENDING", "Pendiente"),
                    ("AVAILABLE", "Disponible"),
                    ("IN_PROGRESS", "En progreso"),
                    ("SUBMITTED", "Enviada"),
                    ("UNDER_REVIEW", "En revisión"),
                    ("COMPLETED", "Completada"),
                    ("REOPENED", "Reabierta"),
                ],
                db_index=True,
                default="PENDING",
                max_length=20,
            ),
        ),
        migrations.CreateModel(
            name="EngagementPhase",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                (
                    "status",
                    models.CharField(
                        choices=[
                            ("PENDING", "Pendiente"),
                            ("AVAILABLE", "Disponible"),
                            ("IN_PROGRESS", "En progreso"),
                            ("SUBMITTED", "Enviada"),
                            ("UNDER_REVIEW", "En revisión"),
                            ("COMPLETED", "Completada"),
                            ("REOPENED", "Reabierta"),
                        ],
                        db_index=True,
                        default="PENDING",
                        max_length=20,
                    ),
                ),
                ("started_at", models.DateTimeField(blank=True, null=True)),
                ("completed_at", models.DateTimeField(blank=True, null=True)),
                ("notes", models.TextField(blank=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                (
                    "completed_by",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="completed_engagement_phases",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
                (
                    "engagement",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="phase_progress",
                        to="programs.engagement",
                    ),
                ),
                (
                    "phase",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="engagement_progress",
                        to="programs.programphase",
                    ),
                ),
            ],
            options={
                "verbose_name": "avance de fase del proceso",
                "verbose_name_plural": "avances de fase del proceso",
                "ordering": ("phase__order", "id"),
            },
        ),
        migrations.CreateModel(
            name="PhaseArtifact",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("file", models.FileField(upload_to="programs.models.phase_artifact_upload_to")),
                ("original_name", models.CharField(max_length=255)),
                ("content_type", models.CharField(blank=True, max_length=120)),
                ("size_bytes", models.PositiveBigIntegerField(default=0)),
                ("description", models.CharField(blank=True, max_length=255)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                (
                    "engagement_phase",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="artifacts",
                        to="programs.engagementphase",
                    ),
                ),
                (
                    "participant_phase",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="artifacts",
                        to="programs.participantphase",
                    ),
                ),
                (
                    "uploaded_by",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="program_phase_artifacts",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
            options={
                "verbose_name": "soporte de fase",
                "verbose_name_plural": "soportes de fase",
                "ordering": ("-created_at",),
            },
        ),
        migrations.CreateModel(
            name="PhaseComment",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("body", models.TextField()),
                ("is_internal", models.BooleanField(default=False)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                (
                    "author",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="program_phase_comments",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
                (
                    "engagement_phase",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="comments",
                        to="programs.engagementphase",
                    ),
                ),
                (
                    "participant_phase",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="comments",
                        to="programs.participantphase",
                    ),
                ),
            ],
            options={
                "verbose_name": "comentario de fase",
                "verbose_name_plural": "comentarios de fase",
                "ordering": ("created_at",),
            },
        ),
        migrations.AddConstraint(
            model_name="engagementphase",
            constraint=models.UniqueConstraint(
                fields=("engagement", "phase"),
                name="engagement_phase_progress_uniq",
            ),
        ),
        migrations.AddConstraint(
            model_name="phaseartifact",
            constraint=models.CheckConstraint(
                condition=(
                    models.Q(("engagement_phase__isnull", True), ("participant_phase__isnull", False))
                    | models.Q(("engagement_phase__isnull", False), ("participant_phase__isnull", True))
                ),
                name="phase_artifact_single_owner",
            ),
        ),
        migrations.AddConstraint(
            model_name="phasecomment",
            constraint=models.CheckConstraint(
                condition=(
                    models.Q(("engagement_phase__isnull", True), ("participant_phase__isnull", False))
                    | models.Q(("engagement_phase__isnull", False), ("participant_phase__isnull", True))
                ),
                name="phase_comment_single_owner",
            ),
        ),
        migrations.RunPython(configure_phase_engine, migrations.RunPython.noop),
    ]
