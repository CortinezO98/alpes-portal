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
