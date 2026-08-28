from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db import transaction
from django.db.models import Avg, Count, F, Q
from django.http import Http404
from django.shortcuts import get_object_or_404, redirect
from django.utils import timezone
from django.views import View
from django.views.generic import FormView, ListView, TemplateView

from apps.accounts.mixins import RoleRequiredMixin
from apps.accounts.models import User

from .forms import AssessmentAssignForm, DimensionAnswerForm, GeneralQuestionsForm
from .models import Assessment, Dimension, Question


class AssessmentManagementListView(
    LoginRequiredMixin,
    RoleRequiredMixin,
    ListView,
):
    template_name = "assessments/management/list.html"
    context_object_name = "assessments"
    allowed_roles = (User.Role.ADMIN, User.Role.SUPERADMIN)
    paginate_by = 20

    def get_queryset(self):
        return Assessment.objects.select_related(
            "template",
            "participant",
            "created_by",
        ).order_by("-created_at")


class AssessmentAssignView(
    LoginRequiredMixin,
    RoleRequiredMixin,
    FormView,
):
    template_name = "assessments/management/assign.html"
    form_class = AssessmentAssignForm
    allowed_roles = (User.Role.ADMIN, User.Role.SUPERADMIN)

    def form_valid(self, form):
        assessment = form.save(commit=False)
        assessment.created_by = self.request.user
        assessment.save()
        messages.success(
            self.request,
            "La evaluación fue asignada correctamente.",
        )
        return redirect("assessments:management-list")


class MyAssessmentListView(LoginRequiredMixin, ListView):
    template_name = "assessments/my/list.html"
    context_object_name = "assessments"

    def get_queryset(self):
        return Assessment.objects.filter(
            participant=self.request.user
        ).select_related("template").order_by("-created_at")


class AssessmentStartView(LoginRequiredMixin, View):
    def post(self, request, pk, *args, **kwargs):
        assessment = get_object_or_404(
            Assessment.objects.select_related("template"),
            pk=pk,
            participant=request.user,
        )
        if assessment.status == Assessment.Status.COMPLETED:
            return redirect("assessments:result", pk=assessment.pk)

        if assessment.status == Assessment.Status.DRAFT:
            assessment.status = Assessment.Status.IN_PROGRESS
            assessment.started_at = assessment.started_at or timezone.now()
            assessment.save(update_fields=("status", "started_at", "updated_at"))

        first_dimension = assessment.template.dimensions.order_by("order", "id").first()
        if not first_dimension:
            raise Http404("La plantilla no tiene dimensiones configuradas.")
        return redirect(
            "assessments:dimension",
            pk=assessment.pk,
            dimension_pk=first_dimension.pk,
        )


class AssessmentDimensionView(LoginRequiredMixin, FormView):
    template_name = "assessments/my/dimension.html"
    form_class = DimensionAnswerForm

    def dispatch(self, request, *args, **kwargs):
        self.assessment = get_object_or_404(
            Assessment.objects.select_related("template"),
            pk=kwargs["pk"],
            participant=request.user,
        )
        if self.assessment.status == Assessment.Status.COMPLETED:
            return redirect("assessments:result", pk=self.assessment.pk)

        self.dimension = get_object_or_404(
            Dimension,
            pk=kwargs["dimension_pk"],
            template=self.assessment.template,
        )
        return super().dispatch(request, *args, **kwargs)

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs.update(
            assessment=self.assessment,
            dimension=self.dimension,
        )
        return kwargs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        dimensions = list(
            self.assessment.template.dimensions.order_by("order", "id")
        )
        current_position = next(
            index
            for index, dimension in enumerate(dimensions, start=1)
            if dimension.pk == self.dimension.pk
        )
        context.update(
            assessment=self.assessment,
            dimension=self.dimension,
            current_position=current_position,
            total_dimensions=len(dimensions),
            progress_percent=round((current_position - 1) / (len(dimensions) + 1) * 100),
        )
        return context

    @transaction.atomic
    def form_valid(self, form):
        if self.assessment.status == Assessment.Status.DRAFT:
            self.assessment.status = Assessment.Status.IN_PROGRESS
            self.assessment.started_at = self.assessment.started_at or timezone.now()
            self.assessment.save(update_fields=("status", "started_at", "updated_at"))

        form.save()
        next_dimension = self.assessment.template.dimensions.filter(
            Q(order__gt=self.dimension.order)
            | Q(order=self.dimension.order, pk__gt=self.dimension.pk)
        ).order_by("order", "id").first()

        if next_dimension:
            return redirect(
                "assessments:dimension",
                pk=self.assessment.pk,
                dimension_pk=next_dimension.pk,
            )
        return redirect("assessments:general", pk=self.assessment.pk)


class AssessmentGeneralQuestionsView(LoginRequiredMixin, FormView):
    template_name = "assessments/my/general.html"
    form_class = GeneralQuestionsForm

    def dispatch(self, request, *args, **kwargs):
        self.assessment = get_object_or_404(
            Assessment.objects.select_related("template"),
            pk=kwargs["pk"],
            participant=request.user,
        )
        if self.assessment.status == Assessment.Status.COMPLETED:
            return redirect("assessments:result", pk=self.assessment.pk)
        return super().dispatch(request, *args, **kwargs)

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["assessment"] = self.assessment
        return kwargs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update(
            assessment=self.assessment,
            progress_percent=89,
        )
        return context

    @transaction.atomic
    def form_valid(self, form):
        required_scale_ids = Question.objects.filter(
            dimension__template=self.assessment.template,
            question_type=Question.Type.SCALE,
            is_required=True,
        ).values_list("pk", flat=True)
        answered_required = self.assessment.answers.filter(
            question_id__in=required_scale_ids,
            score__isnull=False,
        ).count()
        required_count = required_scale_ids.count()

        if answered_required != required_count:
            messages.error(
                self.request,
                "Debes completar todas las dimensiones antes de finalizar.",
            )
            first_incomplete = self.assessment.template.dimensions.annotate(
                required_questions=Count(
                    "questions",
                    filter=Q(
                        questions__question_type=Question.Type.SCALE,
                        questions__is_required=True,
                    ),
                ),
                answered_questions=Count(
                    "questions__answers",
                    filter=Q(
                        questions__answers__assessment=self.assessment,
                        questions__answers__score__isnull=False,
                        questions__question_type=Question.Type.SCALE,
                        questions__is_required=True,
                    ),
                ),
            ).filter(
                answered_questions__lt=F("required_questions")
            ).order_by("order", "id").first()
            if first_incomplete:
                return redirect(
                    "assessments:dimension",
                    pk=self.assessment.pk,
                    dimension_pk=first_incomplete.pk,
                )
            return redirect("assessments:my-list")

        form.save()
        self.assessment.status = Assessment.Status.COMPLETED
        self.assessment.completed_at = timezone.now()
        self.assessment.save(update_fields=("status", "completed_at", "updated_at"))
        messages.success(
            self.request,
            "Tu evaluación fue completada correctamente.",
        )
        return redirect("assessments:result", pk=self.assessment.pk)


class AssessmentResultView(LoginRequiredMixin, TemplateView):
    template_name = "assessments/my/result.html"

    def dispatch(self, request, *args, **kwargs):
        self.assessment = get_object_or_404(
            Assessment.objects.select_related("template"),
            pk=kwargs["pk"],
            participant=request.user,
        )
        if self.assessment.status != Assessment.Status.COMPLETED:
            return redirect("assessments:my-list")
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        dimensions = list(
            self.assessment.template.dimensions.annotate(
                average_score=Avg(
                    "questions__answers__score",
                    filter=Q(questions__answers__assessment=self.assessment),
                )
            ).order_by("order", "id")
        )
        context.update(
            assessment=self.assessment,
            dimensions=dimensions,
            radar_labels=[dimension.name for dimension in dimensions],
            radar_scores=[
                round(float(dimension.average_score or 0), 2)
                for dimension in dimensions
            ],
        )
        return context
