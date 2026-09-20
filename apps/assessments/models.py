from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.db.models import Q


class AssessmentTemplate(models.Model):
    class PublicationStatus(models.TextChoices):
        DRAFT = "DRAFT", "Borrador"
        PUBLISHED = "PUBLISHED", "Publicada"
        RETIRED = "RETIRED", "Retirada"

    name = models.CharField(max_length=160)
    slug = models.SlugField(max_length=180, unique=True)
    description = models.TextField(blank=True)
    version = models.PositiveSmallIntegerField(default=1)
    publication_status = models.CharField(
        max_length=12,
        choices=PublicationStatus.choices,
        default=PublicationStatus.DRAFT,
        db_index=True,
    )
    supersedes = models.ForeignKey(
        "self",
        on_delete=models.PROTECT,
        related_name="successor_versions",
        null=True,
        blank=True,
    )
    published_at = models.DateTimeField(null=True, blank=True)
    is_active = models.BooleanField(default=True, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ("name", "-version")
        constraints = [
            models.UniqueConstraint(
                fields=("supersedes", "version"),
                condition=Q(supersedes__isnull=False),
                name="assess_tpl_supersedes_version_uniq",
            )
        ]
        verbose_name = "plantilla de evaluación"
        verbose_name_plural = "plantillas de evaluación"

    @property
    def is_editable(self):
        return self.publication_status == self.PublicationStatus.DRAFT

    def __str__(self):
        return f"{self.name} · v{self.version}"


class Dimension(models.Model):
    template = models.ForeignKey(
        AssessmentTemplate,
        on_delete=models.CASCADE,
        related_name="dimensions",
    )
    name = models.CharField(max_length=160)
    slug = models.SlugField(max_length=180)
    description = models.TextField(blank=True)
    order = models.PositiveSmallIntegerField(default=1)

    class Meta:
        ordering = ("order", "id")
        constraints = [
            models.UniqueConstraint(
                fields=("template", "slug"),
                name="assessment_dimension_template_slug_unique",
            ),
            models.UniqueConstraint(
                fields=("template", "order"),
                name="assessment_dimension_template_order_unique",
            ),
        ]
        verbose_name = "dimensión"
        verbose_name_plural = "dimensiones"

    def _assert_template_editable(self):
        if self.template_id and not self.template.is_editable:
            raise ValidationError(
                "Las dimensiones de una plantilla publicada no se modifican. "
                "Crea una nueva versión de la plantilla."
            )

    def save(self, *args, **kwargs):
        self._assert_template_editable()
        return super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        self._assert_template_editable()
        return super().delete(*args, **kwargs)

    def __str__(self):
        return f"{self.template.name} · {self.name}"


class Question(models.Model):
    class Type(models.TextChoices):
        SCALE = "SCALE", "Escala de 1 a 10"
        TEXT = "TEXT", "Respuesta abierta"

    dimension = models.ForeignKey(
        Dimension,
        on_delete=models.CASCADE,
        related_name="questions",
        null=True,
        blank=True,
    )
    template = models.ForeignKey(
        AssessmentTemplate,
        on_delete=models.CASCADE,
        related_name="general_questions",
        null=True,
        blank=True,
    )
    text = models.TextField()
    question_type = models.CharField(
        max_length=12,
        choices=Type.choices,
        default=Type.SCALE,
        db_index=True,
    )
    order = models.PositiveSmallIntegerField(default=1)
    is_required = models.BooleanField(default=True)

    class Meta:
        ordering = ("order", "id")
        constraints = [
            models.UniqueConstraint(
                fields=("dimension", "order"),
                name="assessment_question_dimension_order_unique",
            ),
            models.UniqueConstraint(
                fields=("template", "order"),
                condition=Q(dimension__isnull=True),
                name="assess_tpl_order_uniq",
            ),
            models.CheckConstraint(
                condition=(
                    Q(dimension__isnull=False, template__isnull=True)
                    | Q(dimension__isnull=True, template__isnull=False)
                ),
                name="assess_question_parent_xor",
            ),
            models.CheckConstraint(
                condition=(Q(question_type="TEXT") | Q(dimension__isnull=False)),
                name="assess_scale_needs_dim",
            ),
        ]
        verbose_name = "pregunta"
        verbose_name_plural = "preguntas"

    @property
    def assessment_template(self):
        if self.dimension_id:
            return self.dimension.template
        return self.template

    def _assert_template_editable(self):
        template = self.assessment_template
        if template and not template.is_editable:
            raise ValidationError(
                "Las preguntas de una plantilla publicada no se modifican. "
                "Crea una nueva versión de la plantilla."
            )

    def save(self, *args, **kwargs):
        self._assert_template_editable()
        return super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        self._assert_template_editable()
        return super().delete(*args, **kwargs)

    def __str__(self):
        return self.text[:80]


class Assessment(models.Model):
    class Status(models.TextChoices):
        DRAFT = "DRAFT", "Borrador"
        IN_PROGRESS = "IN_PROGRESS", "En progreso"
        COMPLETED = "COMPLETED", "Completada"

    template = models.ForeignKey(
        AssessmentTemplate,
        on_delete=models.PROTECT,
        related_name="assessments",
    )
    participant = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="assessments",
    )
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="created_assessments",
    )
    engagement_participant = models.ForeignKey(
        "programs.EngagementParticipant",
        on_delete=models.PROTECT,
        related_name="assessments",
        null=True,
        blank=True,
    )
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.DRAFT,
        db_index=True,
    )
    started_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ("-created_at",)
        indexes = [
            models.Index(
                fields=("participant", "status"),
                name="assess_part_status_idx",
            )
        ]
        verbose_name = "evaluación"
        verbose_name_plural = "evaluaciones"

    def __str__(self):
        return f"{self.template.name} · {self.participant.email}"


class Answer(models.Model):
    assessment = models.ForeignKey(
        Assessment,
        on_delete=models.CASCADE,
        related_name="answers",
    )
    question = models.ForeignKey(
        Question,
        on_delete=models.PROTECT,
        related_name="answers",
    )
    score = models.PositiveSmallIntegerField(
        null=True,
        blank=True,
        validators=[MinValueValidator(1), MaxValueValidator(10)],
    )
    text = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=("assessment", "question"),
                name="assessment_answer_assessment_question_unique",
            )
        ]
        verbose_name = "respuesta"
        verbose_name_plural = "respuestas"

    def __str__(self):
        return f"Respuesta {self.assessment_id}/{self.question_id}"
