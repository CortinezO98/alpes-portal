import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models
from django.db.models import Q


def seed_jubilacion_plena(apps, schema_editor):
    ServiceProgram = apps.get_model("programs", "ServiceProgram")
    ProgramPhase = apps.get_model("programs", "ProgramPhase")

    program, _ = ServiceProgram.objects.update_or_create(
        code="jubilacion-plena",
        defaults={
            "name": "Jubilación Plena",
            "description": (
                "Acompañamiento a personas próximas a pensionarse en su transición "
                "hacia una nueva etapa de vida con propósito, bienestar y sentido."
            ),
            "is_active": True,
        },
    )

    phases = (
        ("charla-inicial", "Charla y experiencia del consultor", False, True),
        ("rueda-vida", "Rueda de la vida de prepensionados", True, True),
        ("conversaciones", "Conversaciones transformadoras", False, True),
        ("mapa-retos-suenos", "Mapa de retos y sueños", False, True),
        ("plan-accion", "Plan de acción", False, True),
        ("reporte-individual", "Reporte individual", False, True),
        ("reporte-organizacional", "Reporte organizacional", False, False),
    )
    for order, (code, name, automatic, visible) in enumerate(phases, start=1):
        ProgramPhase.objects.update_or_create(
            program=program,
            code=code,
            defaults={
                "name": name,
                "order": order,
                "is_automatic": automatic,
                "participant_visible": visible,
            },
        )


class Migration(migrations.Migration):
    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="Organization",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("name", models.CharField(max_length=180)),
                ("tax_id", models.CharField(blank=True, max_length=40)),
                ("contact_name", models.CharField(blank=True, max_length=160)),
                ("contact_email", models.EmailField(blank=True, max_length=254)),
                ("contact_phone", models.CharField(blank=True, max_length=40)),
                ("city", models.CharField(blank=True, max_length=120)),
                ("notes", models.TextField(blank=True)),
                ("is_active", models.BooleanField(db_index=True, default=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
            ],
            options={"ordering": ("name",), "verbose_name": "organización", "verbose_name_plural": "organizaciones"},
        ),
        migrations.CreateModel(
            name="ServiceProgram",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("code", models.SlugField(max_length=80, unique=True)),
                ("name", models.CharField(max_length=160)),
                ("description", models.TextField(blank=True)),
                ("is_active", models.BooleanField(db_index=True, default=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
            ],
            options={"ordering": ("name",), "verbose_name": "programa de servicio", "verbose_name_plural": "programas de servicio"},
        ),
        migrations.CreateModel(
            name="ProgramPhase",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("code", models.SlugField(max_length=80)),
                ("name", models.CharField(max_length=180)),
                ("description", models.TextField(blank=True)),
                ("order", models.PositiveSmallIntegerField()),
                ("participant_visible", models.BooleanField(default=True)),
                ("is_automatic", models.BooleanField(default=False)),
                ("program", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="phases", to="programs.serviceprogram")),
            ],
            options={"ordering": ("order", "id"), "verbose_name": "fase de programa", "verbose_name_plural": "fases de programa"},
        ),
        migrations.CreateModel(
            name="Engagement",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("title", models.CharField(max_length=200)),
                ("mode", models.CharField(choices=[("INDIVIDUAL", "Individual"), ("ORGANIZATIONAL", "Empresarial")], max_length=20)),
                ("status", models.CharField(choices=[("PLANNING", "Planeación"), ("ACTIVE", "En ejecución"), ("COMPLETED", "Finalizado")], db_index=True, default="PLANNING", max_length=20)),
                ("start_date", models.DateField(blank=True, null=True)),
                ("end_date", models.DateField(blank=True, null=True)),
                ("notes", models.TextField(blank=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("consultant", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="managed_engagements", to=settings.AUTH_USER_MODEL)),
                ("organization", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, related_name="engagements", to="programs.organization")),
                ("program", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="engagements", to="programs.serviceprogram")),
            ],
            options={"ordering": ("-created_at",), "verbose_name": "proceso de acompañamiento", "verbose_name_plural": "procesos de acompañamiento"},
        ),
        migrations.CreateModel(
            name="EngagementParticipant",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("is_active", models.BooleanField(db_index=True, default=True)),
                ("joined_at", models.DateTimeField(auto_now_add=True)),
                ("engagement", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="participants", to="programs.engagement")),
                ("participant", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="program_participations", to=settings.AUTH_USER_MODEL)),
            ],
            options={"ordering": ("participant__email",), "verbose_name": "participante del proceso", "verbose_name_plural": "participantes del proceso"},
        ),
        migrations.CreateModel(
            name="ParticipantPhase",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("status", models.CharField(choices=[("PENDING", "Pendiente"), ("IN_PROGRESS", "En progreso"), ("COMPLETED", "Completada")], db_index=True, default="PENDING", max_length=20)),
                ("started_at", models.DateTimeField(blank=True, null=True)),
                ("completed_at", models.DateTimeField(blank=True, null=True)),
                ("notes", models.TextField(blank=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("completed_by", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="completed_program_phases", to=settings.AUTH_USER_MODEL)),
                ("engagement_participant", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="phase_progress", to="programs.engagementparticipant")),
                ("phase", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="participant_progress", to="programs.programphase")),
            ],
            options={"ordering": ("phase__order", "id"), "verbose_name": "avance de fase", "verbose_name_plural": "avances de fase"},
        ),
        migrations.AddConstraint(
            model_name="programphase",
            constraint=models.UniqueConstraint(fields=("program", "code"), name="program_phase_program_code_uniq"),
        ),
        migrations.AddConstraint(
            model_name="programphase",
            constraint=models.UniqueConstraint(fields=("program", "order"), name="program_phase_program_order_uniq"),
        ),
        migrations.AddConstraint(
            model_name="engagement",
            constraint=models.CheckConstraint(
                condition=Q(mode="INDIVIDUAL", organization__isnull=True) | Q(mode="ORGANIZATIONAL", organization__isnull=False),
                name="engagement_mode_org_consistency",
            ),
        ),
        migrations.AddConstraint(
            model_name="engagementparticipant",
            constraint=models.UniqueConstraint(fields=("engagement", "participant"), name="engagement_participant_uniq"),
        ),
        migrations.AddConstraint(
            model_name="participantphase",
            constraint=models.UniqueConstraint(fields=("engagement_participant", "phase"), name="participant_phase_progress_uniq"),
        ),
        migrations.RunPython(seed_jubilacion_plena, migrations.RunPython.noop),
    ]
