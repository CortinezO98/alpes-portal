from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Avg, Q
from django.shortcuts import get_object_or_404
from django.views.generic import TemplateView

from apps.accounts.mixins import RoleRequiredMixin
from apps.accounts.models import User
from apps.assessments.models import Assessment, Dimension, Question

from .forms import AnalyticsFilterForm


class AnalyticsDashboardView(
    LoginRequiredMixin,
    RoleRequiredMixin,
    TemplateView,
):
    template_name = "reports/dashboard.html"
    allowed_roles = (User.Role.ADMIN, User.Role.SUPERADMIN)

    def _filtered_queryset(self):
        queryset = Assessment.objects.select_related(
            "template",
            "participant",
            "created_by",
        ).order_by("-created_at")

        self.filter_form = AnalyticsFilterForm(self.request.GET or None)
        if not self.filter_form.is_valid():
            return queryset.none()

        status = self.filter_form.cleaned_data.get("status")
        participant = self.filter_form.cleaned_data.get("participant")
        date_from = self.filter_form.cleaned_data.get("date_from")
        date_to = self.filter_form.cleaned_data.get("date_to")

        if status:
            queryset = queryset.filter(status=status)
        if participant:
            queryset = queryset.filter(participant=participant)
        if date_from:
            queryset = queryset.filter(created_at__date__gte=date_from)
        if date_to:
            queryset = queryset.filter(created_at__date__lte=date_to)
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        queryset = self._filtered_queryset()

        total = queryset.count()
        completed = queryset.filter(status=Assessment.Status.COMPLETED)
        completed_count = completed.count()
        in_progress_count = queryset.filter(status=Assessment.Status.IN_PROGRESS).count()
        draft_count = queryset.filter(status=Assessment.Status.DRAFT).count()
        completion_rate = round((completed_count / total) * 100) if total else 0

        dimension_averages = list(
            Dimension.objects.filter(
                questions__answers__assessment__in=completed,
                questions__question_type=Question.Type.SCALE,
            )
            .annotate(
                average_score=Avg(
                    "questions__answers__score",
                    filter=Q(
                        questions__answers__assessment__in=completed,
                        questions__answers__score__isnull=False,
                    ),
                )
            )
            .distinct()
            .order_by("template__name", "order", "id")
        )

        scored_dimensions = [
            dimension
            for dimension in dimension_averages
            if dimension.average_score is not None
        ]
        highest_dimension = max(
            scored_dimensions,
            key=lambda dimension: dimension.average_score,
            default=None,
        )
        lowest_dimension = min(
            scored_dimensions,
            key=lambda dimension: dimension.average_score,
            default=None,
        )

        context.update(
            filter_form=self.filter_form,
            assessments=queryset[:12],
            total_assessments=total,
            completed_count=completed_count,
            in_progress_count=in_progress_count,
            draft_count=draft_count,
            completion_rate=completion_rate,
            dimension_averages=dimension_averages,
            highest_dimension=highest_dimension,
            lowest_dimension=lowest_dimension,
            chart_labels=[dimension.name for dimension in scored_dimensions],
            chart_scores=[round(float(dimension.average_score), 2) for dimension in scored_dimensions],
        )
        return context


class AssessmentReportDetailView(
    LoginRequiredMixin,
    RoleRequiredMixin,
    TemplateView,
):
    template_name = "reports/assessment_detail.html"
    allowed_roles = (User.Role.ADMIN, User.Role.SUPERADMIN)

    def dispatch(self, request, *args, **kwargs):
        self.assessment = get_object_or_404(
            Assessment.objects.select_related("template", "participant", "created_by"),
            pk=kwargs["pk"],
        )
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        dimensions = list(
            self.assessment.template.dimensions.annotate(
                average_score=Avg(
                    "questions__answers__score",
                    filter=Q(
                        questions__answers__assessment=self.assessment,
                        questions__answers__score__isnull=False,
                    ),
                )
            ).order_by("order", "id")
        )
        general_answers = self.assessment.answers.filter(
            question__template=self.assessment.template,
            question__dimension__isnull=True,
        ).select_related("question").order_by("question__order", "question__id")

        context.update(
            assessment=self.assessment,
            dimensions=dimensions,
            general_answers=general_answers,
            radar_labels=[dimension.name for dimension in dimensions],
            radar_scores=[
                round(float(dimension.average_score), 2)
                if dimension.average_score is not None
                else 0
                for dimension in dimensions
            ],
        )
        return context
