from django.conf import settings
from django.db import models


class DimensionAppreciation(models.Model):
    assessment = models.ForeignKey(
        "assessments.Assessment",
        on_delete=models.CASCADE,
        related_name="dimension_appreciations",
    )
    dimension = models.ForeignKey(
        "assessments.Dimension",
        on_delete=models.PROTECT,
        related_name="report_appreciations",
    )
    consultant = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="dimension_appreciations",
    )
    interpretation = models.TextField(blank=True)
    strengths = models.TextField(blank=True)
    opportunities = models.TextField(blank=True)
    recommendation = models.TextField(blank=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=("assessment", "dimension"),
                name="report_dimension_appreciation_uniq",
            )
        ]
        ordering = ("dimension__order", "dimension__id")
        verbose_name = "apreciación por dimensión"
        verbose_name_plural = "apreciaciones por dimensión"

    def __str__(self):
        return f"{self.assessment_id} · {self.dimension.name}"



class IndividualReportVersion(models.Model):
    engagement_participant = models.ForeignKey(
        "programs.EngagementParticipant",
        on_delete=models.CASCADE,
        related_name="individual_report_versions",
    )
    version = models.PositiveSmallIntegerField()
    executive_summary = models.TextField(blank=True)
    integral_appreciation = models.TextField(blank=True)
    recommendations = models.TextField(blank=True)
    conclusions = models.TextField(blank=True)
    snapshot = models.JSONField(default=dict)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="created_individual_report_versions",
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ("-version",)
        constraints = [
            models.UniqueConstraint(
                fields=("engagement_participant", "version"),
                name="individual_report_version_uniq",
            )
        ]
        verbose_name = "versión de reporte individual"
        verbose_name_plural = "versiones de reporte individual"

    def __str__(self):
        return f"{self.engagement_participant} · v{self.version}"


class OrganizationalReportVersion(models.Model):
    engagement = models.ForeignKey(
        "programs.Engagement",
        on_delete=models.CASCADE,
        related_name="organizational_report_versions",
    )
    version = models.PositiveSmallIntegerField()
    executive_summary = models.TextField(blank=True)
    organizational_appreciation = models.TextField(blank=True)
    recommendations = models.TextField(blank=True)
    conclusions = models.TextField(blank=True)
    snapshot = models.JSONField(default=dict)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="created_organizational_report_versions",
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ("-version",)
        constraints = [
            models.UniqueConstraint(
                fields=("engagement", "version"),
                name="organizational_report_version_uniq",
            )
        ]
        verbose_name = "versión de reporte organizacional"
        verbose_name_plural = "versiones de reporte organizacional"

    def __str__(self):
        return f"{self.engagement} · v{self.version}"
