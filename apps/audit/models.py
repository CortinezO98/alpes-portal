from django.conf import settings
from django.db import models


class AuditEvent(models.Model):
    class Action(models.TextChoices):
        LOGIN_SUCCESS = "login_success", "Inicio de sesión exitoso"
        LOGIN_FAILURE = "login_failure", "Inicio de sesión fallido"
        PASSWORD_RESET_REQUEST = "password_reset_request", "Solicitud de recuperación"
        USER_CREATED = "user_created", "Usuario creado"
        USER_UPDATED = "user_updated", "Usuario actualizado"
        USER_STATUS_CHANGED = "user_status_changed", "Estado de usuario modificado"

    actor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="audit_events",
    )
    action = models.CharField(max_length=64, choices=Action.choices, db_index=True)
    target_type = models.CharField(max_length=64, blank=True)
    target_id = models.CharField(max_length=64, blank=True)
    target_label = models.CharField(max_length=255, blank=True)
    ip_hash = models.CharField(max_length=64, blank=True, db_index=True)
    metadata = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        ordering = ("-created_at", "-id")
        indexes = [
            models.Index(fields=("action", "created_at"), name="audit_action_created_idx"),
        ]

    def __str__(self):
        return f"{self.action} @ {self.created_at:%Y-%m-%d %H:%M:%S}"


class AuthThrottle(models.Model):
    scope = models.CharField(max_length=32)
    key_hash = models.CharField(max_length=64)
    window_started_at = models.DateTimeField()
    attempts = models.PositiveSmallIntegerField(default=0)
    blocked_until = models.DateTimeField(null=True, blank=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=("scope", "key_hash"),
                name="audit_auth_throttle_scope_key_uniq",
            ),
        ]
        indexes = [
            models.Index(fields=("scope", "key_hash"), name="audit_throttle_lookup_idx"),
        ]

    def __str__(self):
        return f"{self.scope}:{self.key_hash[:8]}"
