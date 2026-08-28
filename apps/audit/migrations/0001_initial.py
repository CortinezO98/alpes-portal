import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):
    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="AuthThrottle",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("scope", models.CharField(max_length=32)),
                ("key_hash", models.CharField(max_length=64)),
                ("window_started_at", models.DateTimeField()),
                ("attempts", models.PositiveSmallIntegerField(default=0)),
                ("blocked_until", models.DateTimeField(blank=True, null=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
            ],
        ),
        migrations.CreateModel(
            name="AuditEvent",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("action", models.CharField(choices=[("login_success", "Inicio de sesión exitoso"), ("login_failure", "Inicio de sesión fallido"), ("password_reset_request", "Solicitud de recuperación"), ("user_created", "Usuario creado"), ("user_updated", "Usuario actualizado"), ("user_status_changed", "Estado de usuario modificado")], db_index=True, max_length=64)),
                ("target_type", models.CharField(blank=True, max_length=64)),
                ("target_id", models.CharField(blank=True, max_length=64)),
                ("target_label", models.CharField(blank=True, max_length=255)),
                ("ip_hash", models.CharField(blank=True, db_index=True, max_length=64)),
                ("metadata", models.JSONField(blank=True, default=dict)),
                ("created_at", models.DateTimeField(auto_now_add=True, db_index=True)),
                ("actor", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="audit_events", to=settings.AUTH_USER_MODEL)),
            ],
            options={"ordering": ("-created_at", "-id")},
        ),
        migrations.AddConstraint(
            model_name="auththrottle",
            constraint=models.UniqueConstraint(fields=("scope", "key_hash"), name="audit_auth_throttle_scope_key_uniq"),
        ),
        migrations.AddIndex(
            model_name="auththrottle",
            index=models.Index(fields=["scope", "key_hash"], name="audit_throttle_lookup_idx"),
        ),
        migrations.AddIndex(
            model_name="auditevent",
            index=models.Index(fields=["action", "created_at"], name="audit_action_created_idx"),
        ),
    ]
