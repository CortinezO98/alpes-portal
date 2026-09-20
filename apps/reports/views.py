from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Avg, Q
from django.contrib import messages
from django.shortcuts import get_object_or_404, redirect
from django.views import View
from django.views.generic import TemplateView

from apps.accounts.mixins import RoleRequiredMixin
from apps.accounts.models import User
from apps.assessments.models import Assessment, Dimension, Question

from .forms import AnalyticsFilterForm, DimensionAppreciationForm
from .models import DimensionAppreciation
from .services.report_builder import build_assessment_report


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

        self.filter_form = AnalyticsFilterForm(self.request.GET)
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
        report = build_assessment_report(self.assessment)
        context.update(
            assessment=self.assessment,
            report_dimensions=report["dimensions"],
            general_answers=report["general_answers"],
            radar_dimensions=report["radar"],
            template_version=self.assessment.template.version,
        )
        return context



class DimensionAppreciationUpdateView(
    LoginRequiredMixin,
    RoleRequiredMixin,
    View,
):
    allowed_roles = (User.Role.ADMIN, User.Role.SUPERADMIN)

    def post(self, request, assessment_pk, dimension_pk):
        assessment = get_object_or_404(
            Assessment.objects.select_related("template"),
            pk=assessment_pk,
        )
        dimension = get_object_or_404(
            Dimension,
            pk=dimension_pk,
            template=assessment.template,
        )
        instance = DimensionAppreciation.objects.filter(
            assessment=assessment,
            dimension=dimension,
        ).first()
        form = DimensionAppreciationForm(request.POST, instance=instance)
        if not form.is_valid():
            messages.error(
                request,
                "No fue posible guardar la apreciación. Revisa la información ingresada.",
            )
            return redirect("reports:assessment-detail", pk=assessment.pk)

        appreciation = form.save(commit=False)
        appreciation.assessment = assessment
        appreciation.dimension = dimension
        appreciation.consultant = request.user
        appreciation.save()

        messages.success(
            request,
            f"La apreciación de “{dimension.name}” fue guardada correctamente.",
        )
        return redirect("reports:assessment-detail", pk=assessment.pk)
