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
    class Scope(models.TextChoices):
        PARTICIPANT = "PARTICIPANT", "Participante"
        ENGAGEMENT = "ENGAGEMENT", "Proceso / empresa"

    program = models.ForeignKey(ServiceProgram, on_delete=models.CASCADE, related_name="phases")
    code = models.SlugField(max_length=80)
    name = models.CharField(max_length=180)
    description = models.TextField(blank=True)
    order = models.PositiveSmallIntegerField()
    participant_visible = models.BooleanField(default=True)
    is_automatic = models.BooleanField(default=False)
    scope = models.CharField(max_length=20, choices=Scope.choices, default=Scope.PARTICIPANT)
    allows_artifacts = models.BooleanField(default=True)
    requires_artifact = models.BooleanField(default=False)
    requires_review = models.BooleanField(default=True)

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
        phases = list(self.phase_progress.filter(phase__scope=ProgramPhase.Scope.PARTICIPANT))
        total = len(phases)
        if not total:
            return 0
        completed = sum(1 for item in phases if item.status == ParticipantPhase.Status.COMPLETED)
        return round((completed / total) * 100)


class ParticipantPhase(models.Model):
    class Status(models.TextChoices):
        PENDING = "PENDING", "Pendiente"
        AVAILABLE = "AVAILABLE", "Disponible"
        IN_PROGRESS = "IN_PROGRESS", "En progreso"
        SUBMITTED = "SUBMITTED", "Enviada"
        UNDER_REVIEW = "UNDER_REVIEW", "En revisión"
        COMPLETED = "COMPLETED", "Completada"
        REOPENED = "REOPENED", "Reabierta"

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


class EngagementPhase(models.Model):
    engagement = models.ForeignKey(
        Engagement, on_delete=models.CASCADE, related_name="phase_progress"
    )
    phase = models.ForeignKey(
        ProgramPhase, on_delete=models.PROTECT, related_name="engagement_progress"
    )
    status = models.CharField(
        max_length=20,
        choices=ParticipantPhase.Status.choices,
        default=ParticipantPhase.Status.PENDING,
        db_index=True,
    )
    started_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    completed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        related_name="completed_engagement_phases",
        null=True,
        blank=True,
    )
    notes = models.TextField(blank=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ("phase__order", "id")
        constraints = [
            models.UniqueConstraint(
                fields=("engagement", "phase"),
                name="engagement_phase_progress_uniq",
            )
        ]
        verbose_name = "avance de fase del proceso"
        verbose_name_plural = "avances de fase del proceso"

    def __str__(self):
        return f"{self.engagement} · {self.phase.name}"


def phase_artifact_upload_to(instance, filename):
    if instance.participant_phase_id:
        progress = instance.participant_phase
        engagement_id = progress.engagement_participant.engagement_id
        owner = f"participant-{progress.engagement_participant_id}"
        phase_code = progress.phase.code
    else:
        progress = instance.engagement_phase
        engagement_id = progress.engagement_id
        owner = "engagement"
        phase_code = progress.phase.code
    return f"programs/{engagement_id}/{owner}/{phase_code}/{filename}"


class PhaseArtifact(models.Model):
    participant_phase = models.ForeignKey(
        ParticipantPhase,
        on_delete=models.CASCADE,
        related_name="artifacts",
        null=True,
        blank=True,
    )
    engagement_phase = models.ForeignKey(
        EngagementPhase,
        on_delete=models.CASCADE,
        related_name="artifacts",
        null=True,
        blank=True,
    )
    file = models.FileField(upload_to=phase_artifact_upload_to)
    original_name = models.CharField(max_length=255)
    content_type = models.CharField(max_length=120, blank=True)
    size_bytes = models.PositiveBigIntegerField(default=0)
    description = models.CharField(max_length=255, blank=True)
    uploaded_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="program_phase_artifacts",
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ("-created_at",)
        constraints = [
            models.CheckConstraint(
                condition=(
                    Q(participant_phase__isnull=False, engagement_phase__isnull=True)
                    | Q(participant_phase__isnull=True, engagement_phase__isnull=False)
                ),
                name="phase_artifact_single_owner",
            )
        ]
        verbose_name = "soporte de fase"
        verbose_name_plural = "soportes de fase"


class PhaseComment(models.Model):
    participant_phase = models.ForeignKey(
        ParticipantPhase,
        on_delete=models.CASCADE,
        related_name="comments",
        null=True,
        blank=True,
    )
    engagement_phase = models.ForeignKey(
        EngagementPhase,
        on_delete=models.CASCADE,
        related_name="comments",
        null=True,
        blank=True,
    )
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="program_phase_comments",
    )
    body = models.TextField()
    is_internal = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ("created_at",)
        constraints = [
            models.CheckConstraint(
                condition=(
                    Q(participant_phase__isnull=False, engagement_phase__isnull=True)
                    | Q(participant_phase__isnull=True, engagement_phase__isnull=False)
                ),
                name="phase_comment_single_owner",
            )
        ]
        verbose_name = "comentario de fase"
        verbose_name_plural = "comentarios de fase"



class ConsultantExperienceRecord(models.Model):
    participant_phase = models.OneToOneField(
        ParticipantPhase,
        on_delete=models.CASCADE,
        related_name="consultant_experience",
    )
    session_date = models.DateField()
    topic = models.CharField(max_length=180)
    consultant_experience = models.TextField(blank=True)
    participant_learnings = models.TextField(blank=True)
    commitments = models.TextField(blank=True)
    consultant_appreciation = models.TextField(blank=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="created_consultant_experiences",
    )
    updated_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="updated_consultant_experiences",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "registro de charla y experiencia"
        verbose_name_plural = "registros de charla y experiencia"

    def __str__(self):
        return f"{self.session_date} · {self.topic}"


class TransformationSession(models.Model):
    participant_phase = models.ForeignKey(
        ParticipantPhase,
        on_delete=models.CASCADE,
        related_name="transformation_sessions",
    )
    session_date = models.DateField()
    title = models.CharField(max_length=180)
    topics = models.TextField(blank=True)
    findings = models.TextField(blank=True)
    commitments = models.TextField(blank=True)
    consultant_appreciation = models.TextField(blank=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="created_transformation_sessions",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ("session_date", "id")
        verbose_name = "sesión transformadora"
        verbose_name_plural = "sesiones transformadoras"

    def __str__(self):
        return f"{self.session_date} · {self.title}"


class DreamChallengeNode(models.Model):
    class NodeType(models.TextChoices):
        DREAM = "DREAM", "Sueño"
        CHALLENGE = "CHALLENGE", "Reto"
        GOAL = "GOAL", "Meta"
        MILESTONE = "MILESTONE", "Hito"

    class Priority(models.TextChoices):
        LOW = "LOW", "Baja"
        MEDIUM = "MEDIUM", "Media"
        HIGH = "HIGH", "Alta"

    participant_phase = models.ForeignKey(
        ParticipantPhase,
        on_delete=models.CASCADE,
        related_name="dream_map_nodes",
    )
    parent = models.ForeignKey(
        "self",
        on_delete=models.CASCADE,
        related_name="children",
        null=True,
        blank=True,
    )
    node_type = models.CharField(max_length=20, choices=NodeType.choices)
    title = models.CharField(max_length=180)
    description = models.TextField(blank=True)
    priority = models.CharField(
        max_length=10,
        choices=Priority.choices,
        default=Priority.MEDIUM,
    )
    target_date = models.DateField(null=True, blank=True)
    order = models.PositiveSmallIntegerField(default=1)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="created_dream_map_nodes",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ("order", "id")
        verbose_name = "nodo de retos y sueños"
        verbose_name_plural = "nodos de retos y sueños"

    def __str__(self):
        return f"{self.get_node_type_display()} · {self.title}"


class ActionPlanGoal(models.Model):
    participant_phase = models.ForeignKey(
        ParticipantPhase,
        on_delete=models.CASCADE,
        related_name="action_goals",
    )
    source_node = models.ForeignKey(
        DreamChallengeNode,
        on_delete=models.SET_NULL,
        related_name="linked_action_goals",
        null=True,
        blank=True,
    )
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    target_date = models.DateField(null=True, blank=True)
    order = models.PositiveSmallIntegerField(default=1)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="created_action_plan_goals",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ("order", "id")
        verbose_name = "meta del plan de acción"
        verbose_name_plural = "metas del plan de acción"

    def __str__(self):
        return self.title


class ActionPlanItem(models.Model):
    class Status(models.TextChoices):
        PENDING = "PENDING", "Pendiente"
        IN_PROGRESS = "IN_PROGRESS", "En curso"
        COMPLETED = "COMPLETED", "Completada"

    goal = models.ForeignKey(
        ActionPlanGoal,
        on_delete=models.CASCADE,
        related_name="items",
    )
    action = models.CharField(max_length=240)
    indicator = models.CharField(max_length=240, blank=True)
    responsible = models.CharField(max_length=180, blank=True)
    due_date = models.DateField(null=True, blank=True)
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.PENDING,
    )
    consultant_appreciation = models.TextField(blank=True)
    order = models.PositiveSmallIntegerField(default=1)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="created_action_plan_items",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ("order", "id")
        verbose_name = "acción del plan"
        verbose_name_plural = "acciones del plan"

    def __str__(self):
        return self.action
