from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ("programs", "0002_phase_workflow_engine"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="TransformationSession",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("session_date", models.DateField()),
                ("title", models.CharField(max_length=180)),
                ("topics", models.TextField(blank=True)),
                ("findings", models.TextField(blank=True)),
                ("commitments", models.TextField(blank=True)),
                ("consultant_appreciation", models.TextField(blank=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("created_by", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="created_transformation_sessions", to=settings.AUTH_USER_MODEL)),
                ("participant_phase", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="transformation_sessions", to="programs.participantphase")),
            ],
            options={"ordering": ("session_date", "id"), "verbose_name": "sesión transformadora", "verbose_name_plural": "sesiones transformadoras"},
        ),
        migrations.CreateModel(
            name="DreamChallengeNode",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("node_type", models.CharField(choices=[("DREAM", "Sueño"), ("CHALLENGE", "Reto"), ("GOAL", "Meta"), ("MILESTONE", "Hito")], max_length=20)),
                ("title", models.CharField(max_length=180)),
                ("description", models.TextField(blank=True)),
                ("priority", models.CharField(choices=[("LOW", "Baja"), ("MEDIUM", "Media"), ("HIGH", "Alta")], default="MEDIUM", max_length=10)),
                ("target_date", models.DateField(blank=True, null=True)),
                ("order", models.PositiveSmallIntegerField(default=1)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("created_by", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="created_dream_map_nodes", to=settings.AUTH_USER_MODEL)),
                ("parent", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name="children", to="programs.dreamchallengenode")),
                ("participant_phase", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="dream_map_nodes", to="programs.participantphase")),
            ],
            options={"ordering": ("order", "id"), "verbose_name": "nodo de retos y sueños", "verbose_name_plural": "nodos de retos y sueños"},
        ),
        migrations.CreateModel(
            name="ActionPlanGoal",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("title", models.CharField(max_length=200)),
                ("description", models.TextField(blank=True)),
                ("target_date", models.DateField(blank=True, null=True)),
                ("order", models.PositiveSmallIntegerField(default=1)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("created_by", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="created_action_plan_goals", to=settings.AUTH_USER_MODEL)),
                ("participant_phase", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="action_goals", to="programs.participantphase")),
            ],
            options={"ordering": ("order", "id"), "verbose_name": "meta del plan de acción", "verbose_name_plural": "metas del plan de acción"},
        ),
        migrations.CreateModel(
            name="ActionPlanItem",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("action", models.CharField(max_length=240)),
                ("indicator", models.CharField(blank=True, max_length=240)),
                ("responsible", models.CharField(blank=True, max_length=180)),
                ("due_date", models.DateField(blank=True, null=True)),
                ("status", models.CharField(choices=[("PENDING", "Pendiente"), ("IN_PROGRESS", "En curso"), ("COMPLETED", "Completada")], default="PENDING", max_length=20)),
                ("consultant_appreciation", models.TextField(blank=True)),
                ("order", models.PositiveSmallIntegerField(default=1)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("created_by", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="created_action_plan_items", to=settings.AUTH_USER_MODEL)),
                ("goal", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="items", to="programs.actionplangoal")),
            ],
            options={"ordering": ("order", "id"), "verbose_name": "acción del plan", "verbose_name_plural": "acciones del plan"},
        ),
    ]
