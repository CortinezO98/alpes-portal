from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
from django.db.models import Q


class Organization(models.Model):
    name = models.CharField(max_length=180)
    tax_id = models.CharField(max_length=40, blank=True)
    contact_name = models.CharField(max_length=160, blank=True)
    contact_email = models.EmailField(blank=True)
    contact_phone = models.CharField(max_length=40, blank=True)
    city = models.CharField(max_length=120, blank=True)
    notes = models.TextField(blank=True)
    is_active = models.BooleanField(default=True, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ("name",)
        verbose_name = "organización"
        verbose_name_plural = "organizaciones"

    def __str__(self):
        return self.name


class ServiceProgram(models.Model):
    code = models.SlugField(max_length=80, unique=True)
    name = models.CharField(max_length=160)
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ("name",)
        verbose_name = "programa de servicio"
        verbose_name_plural = "programas de servicio"

    def __str__(self):
        return self.name


class ProgramPhase(models.Model):
    program = models.ForeignKey(ServiceProgram, on_delete=models.CASCADE, related_name="phases")
    code = models.SlugField(max_length=80)
    name = models.CharField(max_length=180)
    description = models.TextField(blank=True)
    order = models.PositiveSmallIntegerField()
    participant_visible = models.BooleanField(default=True)
    is_automatic = models.BooleanField(default=False)

    class Meta:
        ordering = ("order", "id")
        constraints = [
            models.UniqueConstraint(fields=("program", "code"), name="program_phase_program_code_uniq"),
            models.UniqueConstraint(fields=("program", "order"), name="program_phase_program_order_uniq"),
        ]
        verbose_name = "fase de programa"
        verbose_name_plural = "fases de programa"

    def __str__(self):
        return f"{self.program.name} · {self.order}. {self.name}"


class Engagement(models.Model):
    class Mode(models.TextChoices):
        INDIVIDUAL = "INDIVIDUAL", "Individual"
        ORGANIZATIONAL = "ORGANIZATIONAL", "Empresarial"

    class Status(models.TextChoices):
        PLANNING = "PLANNING", "Planeación"
        ACTIVE = "ACTIVE", "En ejecución"
        COMPLETED = "COMPLETED", "Finalizado"

    title = models.CharField(max_length=200)
    program = models.ForeignKey(ServiceProgram, on_delete=models.PROTECT, related_name="engagements")
    mode = models.CharField(max_length=20, choices=Mode.choices)
    organization = models.ForeignKey(
        Organization, on_delete=models.PROTECT, related_name="engagements", null=True, blank=True
    )
    consultant = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="managed_engagements"
    )
    status = models.CharField(
        max_length=20, choices=Status.choices, default=Status.PLANNING, db_index=True
    )
    start_date = models.DateField(null=True, blank=True)
    end_date = models.DateField(null=True, blank=True)
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ("-created_at",)
        constraints = [
            models.CheckConstraint(
                condition=(
                    Q(mode="INDIVIDUAL", organization__isnull=True)
                    | Q(mode="ORGANIZATIONAL", organization__isnull=False)
                ),
                name="engagement_mode_org_consistency",
            )
        ]
        verbose_name = "proceso de acompañamiento"
        verbose_name_plural = "procesos de acompañamiento"

    def clean(self):
        super().clean()
        if self.mode == self.Mode.ORGANIZATIONAL and not self.organization_id:
            raise ValidationError({"organization": "Selecciona una organización para un proceso empresarial."})
        if self.mode == self.Mode.INDIVIDUAL and self.organization_id:
            raise ValidationError({"organization": "Un proceso individual no debe tener organización."})

    def __str__(self):
        return self.title


class EngagementParticipant(models.Model):
    engagement = models.ForeignKey(Engagement, on_delete=models.CASCADE, related_name="participants")
    participant = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="program_participations"
    )
    is_active = models.BooleanField(default=True, db_index=True)
    joined_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ("participant__email",)
        constraints = [
            models.UniqueConstraint(
                fields=("engagement", "participant"),
                name="engagement_participant_uniq",
            )
        ]
        verbose_name = "participante del proceso"
        verbose_name_plural = "participantes del proceso"

    def __str__(self):
        return f"{self.engagement.title} · {self.participant.email}"

    @property
    def progress_percent(self):
        phases = list(self.phase_progress.all())
        total = len(phases)
        if not total:
            return 0
        completed = sum(1 for item in phases if item.status == ParticipantPhase.Status.COMPLETED)
        return round((completed / total) * 100)


class ParticipantPhase(models.Model):
    class Status(models.TextChoices):
        PENDING = "PENDING", "Pendiente"
        IN_PROGRESS = "IN_PROGRESS", "En progreso"
        COMPLETED = "COMPLETED", "Completada"

    engagement_participant = models.ForeignKey(
        EngagementParticipant, on_delete=models.CASCADE, related_name="phase_progress"
    )
    phase = models.ForeignKey(ProgramPhase, on_delete=models.PROTECT, related_name="participant_progress")
    status = models.CharField(
        max_length=20, choices=Status.choices, default=Status.PENDING, db_index=True
    )
    started_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    completed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        related_name="completed_program_phases",
        null=True,
        blank=True,
    )
    notes = models.TextField(blank=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ("phase__order", "id")
        constraints = [
            models.UniqueConstraint(
                fields=("engagement_participant", "phase"),
                name="participant_phase_progress_uniq",
            )
        ]
        verbose_name = "avance de fase"
        verbose_name_plural = "avances de fase"

    def __str__(self):
        return f"{self.engagement_participant} · {self.phase.name}"
