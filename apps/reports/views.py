from django.contrib.auth.mixins import LoginRequiredMixin
from django.db import transaction
from django.db.models import Avg, Max, Q
from django.contrib import messages
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse
from django.views import View
from django.views.generic import TemplateView

from apps.accounts.mixins import RoleRequiredMixin
from apps.accounts.models import User
from apps.assessments.models import Assessment, Dimension, Question
from apps.programs.models import Engagement, EngagementParticipant
from apps.programs.services import (
    complete_generated_individual_report,
    complete_generated_organizational_report,
)

from .forms import (
    AnalyticsFilterForm,
    DimensionAppreciationForm,
    IndividualReportVersionForm,
    OrganizationalReportVersionForm,
)
from .models import DimensionAppreciation, IndividualReportVersion, OrganizationalReportVersion
from .services.report_builder import build_assessment_report
from .services.program_report_builder import (
    build_individual_program_snapshot,
    build_organizational_program_snapshot,
)


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



def _is_report_admin(user):
    return bool(
        user.is_authenticated
        and (
            user.is_superuser
            or user.role in {User.Role.ADMIN, User.Role.SUPERADMIN}
        )
    )


class IndividualProgramReportView(LoginRequiredMixin, TemplateView):
    template_name = "reports/program_individual.html"

    def dispatch(self, request, *args, **kwargs):
        queryset = EngagementParticipant.objects.select_related(
            "participant",
            "engagement__program",
            "engagement__organization",
            "engagement__consultant",
        ).prefetch_related(
            "individual_report_versions",
            "phase_progress__phase",
        )
        self.participation = get_object_or_404(queryset, pk=kwargs["pk"])
        if not (
            _is_report_admin(request.user)
            or self.participation.participant_id == request.user.id
        ):
            from django.core.exceptions import PermissionDenied
            raise PermissionDenied
        return super().dispatch(request, *args, **kwargs)

    def _selected_version(self):
        versions = self.participation.individual_report_versions.all()
        requested = self.request.GET.get("version")
        if requested and str(requested).isdigit():
            return versions.filter(version=int(requested)).first()
        return versions.first()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        selected = self._selected_version()
        latest = self.participation.individual_report_versions.first()
        context.update(
            participation=self.participation,
            engagement=self.participation.engagement,
            report_version=selected,
            report_versions=self.participation.individual_report_versions.all(),
            is_report_admin=_is_report_admin(self.request.user),
            report_form=IndividualReportVersionForm(
                initial={
                    "executive_summary": latest.executive_summary if latest else "",
                    "integral_appreciation": latest.integral_appreciation if latest else "",
                    "recommendations": latest.recommendations if latest else "",
                    "conclusions": latest.conclusions if latest else "",
                }
            ),
        )
        return context


class IndividualProgramReportGenerateView(
    LoginRequiredMixin,
    RoleRequiredMixin,
    View,
):
    allowed_roles = (User.Role.ADMIN, User.Role.SUPERADMIN)

    @transaction.atomic
    def post(self, request, pk):
        participation = get_object_or_404(
            EngagementParticipant.objects.select_for_update().select_related(
                "participant",
                "engagement__program",
                "engagement__organization",
                "engagement__consultant",
            ),
            pk=pk,
        )
        form = IndividualReportVersionForm(request.POST)
        if not form.is_valid():
            messages.error(request, "Revisa los campos del reporte antes de generar la versión.")
            return redirect("reports:program-individual", pk=participation.pk)

        try:
            complete_generated_individual_report(participation, request.user)
        except ValueError as exc:
            messages.error(request, str(exc))
            return redirect("reports:program-individual", pk=participation.pk)

        snapshot = build_individual_program_snapshot(participation)
        current = (
            participation.individual_report_versions.aggregate(max_version=Max("version"))[
                "max_version"
            ]
            or 0
        )
        report = form.save(commit=False)
        report.engagement_participant = participation
        report.version = current + 1
        report.snapshot = snapshot
        report.created_by = request.user
        report.save()

        messages.success(
            request,
            f"Reporte individual v{report.version} generado correctamente.",
        )
        return redirect(
            f"{reverse('reports:program-individual', kwargs={'pk': participation.pk})}?version={report.version}"
        )


class OrganizationalProgramReportView(
    LoginRequiredMixin,
    RoleRequiredMixin,
    TemplateView,
):
    template_name = "reports/program_organizational.html"
    allowed_roles = (User.Role.ADMIN, User.Role.SUPERADMIN)

    def dispatch(self, request, *args, **kwargs):
        self.engagement = get_object_or_404(
            Engagement.objects.select_related(
                "program", "organization", "consultant"
            ).prefetch_related("organizational_report_versions", "participants"),
            pk=kwargs["pk"],
            mode=Engagement.Mode.ORGANIZATIONAL,
        )
        return super().dispatch(request, *args, **kwargs)

    def _selected_version(self):
        versions = self.engagement.organizational_report_versions.all()
        requested = self.request.GET.get("version")
        if requested and str(requested).isdigit():
            return versions.filter(version=int(requested)).first()
        return versions.first()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        selected = self._selected_version()
        latest = self.engagement.organizational_report_versions.first()
        context.update(
            engagement=self.engagement,
            report_version=selected,
            report_versions=self.engagement.organizational_report_versions.all(),
            report_form=OrganizationalReportVersionForm(
                initial={
                    "executive_summary": latest.executive_summary if latest else "",
                    "organizational_appreciation": latest.organizational_appreciation if latest else "",
                    "recommendations": latest.recommendations if latest else "",
                    "conclusions": latest.conclusions if latest else "",
                }
            ),
        )
        return context


class OrganizationalProgramReportGenerateView(
    LoginRequiredMixin,
    RoleRequiredMixin,
    View,
):
    allowed_roles = (User.Role.ADMIN, User.Role.SUPERADMIN)

    @transaction.atomic
    def post(self, request, pk):
        engagement = get_object_or_404(
            Engagement.objects.select_for_update().select_related(
                "program", "organization", "consultant"
            ),
            pk=pk,
            mode=Engagement.Mode.ORGANIZATIONAL,
        )
        form = OrganizationalReportVersionForm(request.POST)
        if not form.is_valid():
            messages.error(request, "Revisa los campos del reporte organizacional.")
            return redirect("reports:program-organizational", pk=engagement.pk)

        try:
            complete_generated_organizational_report(engagement, request.user)
        except ValueError as exc:
            messages.error(request, str(exc))
            return redirect("reports:program-organizational", pk=engagement.pk)

        snapshot = build_organizational_program_snapshot(engagement)
        current = (
            engagement.organizational_report_versions.aggregate(max_version=Max("version"))[
                "max_version"
            ]
            or 0
        )
        report = form.save(commit=False)
        report.engagement = engagement
        report.version = current + 1
        report.snapshot = snapshot
        report.created_by = request.user
        report.save()

        messages.success(
            request,
            f"Reporte organizacional v{report.version} generado correctamente.",
        )
        return redirect(
            f"{reverse('reports:program-organizational', kwargs={'pk': engagement.pk})}?version={report.version}"
        )
