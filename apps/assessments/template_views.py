from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.exceptions import ValidationError
from django.http import Http404
from django.shortcuts import get_object_or_404, redirect
from django.views import View
from django.views.generic import FormView, ListView, TemplateView

from apps.accounts.mixins import RoleRequiredMixin
from apps.accounts.models import User

from .forms import (
    DimensionConfigForm,
    GeneralQuestionConfigForm,
    ScaleQuestionConfigForm,
)
from .models import AssessmentTemplate, Dimension, Question
from .services.template_versioning import create_next_template_version, publish_template


class TemplateSuperAdminMixin(LoginRequiredMixin, RoleRequiredMixin):
    allowed_roles = (User.Role.SUPERADMIN,)


class TemplateConfigurationListView(TemplateSuperAdminMixin, ListView):
    template_name = "assessments/templates/list.html"
    context_object_name = "templates"

    def get_queryset(self):
        return AssessmentTemplate.objects.select_related("supersedes").prefetch_related(
            "dimensions"
        ).order_by("name", "-version")


class TemplateConfigurationDetailView(TemplateSuperAdminMixin, TemplateView):
    template_name = "assessments/templates/detail.html"

    def dispatch(self, request, *args, **kwargs):
        self.template_object = get_object_or_404(
            AssessmentTemplate.objects.select_related("supersedes").prefetch_related(
                "dimensions__questions",
                "general_questions",
            ),
            pk=kwargs["pk"],
        )
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update(
            template_object=self.template_object,
            dimensions=self.template_object.dimensions.all().order_by("order", "id"),
            general_questions=self.template_object.general_questions.order_by("order", "id"),
        )
        return context

    @staticmethod
    def _form_error_message(form):
        errors = []
        for field, field_errors in form.errors.items():
            label = form.fields[field].label if field in form.fields else "Formulario"
            errors.extend(f"{label}: {error}" for error in field_errors)
        return " ".join(errors) or "Revisa los datos ingresados."

    def post(self, request, *args, **kwargs):
        if not self.template_object.is_editable:
            raise Http404("La versión publicada es de solo lectura.")

        action = request.POST.get("action")

        if action == "create-scale-question":
            dimension = get_object_or_404(
                Dimension,
                pk=request.POST.get("dimension_id"),
                template=self.template_object,
            )
            form = ScaleQuestionConfigForm(request.POST, dimension=dimension)
            if form.is_valid():
                form.save()
                messages.success(request, f"Se agregó un nuevo ítem a {dimension.name}.")
            else:
                messages.error(request, self._form_error_message(form))
            return redirect("assessments:template-detail", pk=self.template_object.pk)

        if action == "update-scale-question":
            question = get_object_or_404(
                Question.objects.select_related("dimension"),
                pk=request.POST.get("question_id"),
                dimension__template=self.template_object,
                dimension__isnull=False,
                question_type=Question.Type.SCALE,
            )
            form = ScaleQuestionConfigForm(
                request.POST,
                dimension=question.dimension,
                instance=question,
            )
            if form.is_valid():
                form.save()
                messages.success(request, "El ítem fue actualizado correctamente.")
            else:
                messages.error(request, self._form_error_message(form))
            return redirect("assessments:template-detail", pk=self.template_object.pk)

        raise Http404("Acción de configuración no reconocida.")


class TemplateCreateVersionView(TemplateSuperAdminMixin, View):
    def post(self, request, pk, *args, **kwargs):
        source = get_object_or_404(AssessmentTemplate, pk=pk)
        try:
            new_version = create_next_template_version(source)
        except ValidationError as exc:
            messages.error(request, "; ".join(exc.messages))
            return redirect("assessments:template-detail", pk=source.pk)

        messages.success(
            request,
            f"Se creó la versión {new_version.version} como borrador. "
            "La versión publicada actual continúa vigente hasta que publiques la nueva.",
        )
        return redirect("assessments:template-detail", pk=new_version.pk)


class TemplatePublishView(TemplateSuperAdminMixin, View):
    def post(self, request, pk, *args, **kwargs):
        template = get_object_or_404(AssessmentTemplate, pk=pk)
        try:
            publish_template(template)
        except ValidationError as exc:
            messages.error(request, "; ".join(exc.messages))
        else:
            messages.success(
                request,
                f"La versión {template.version} fue publicada correctamente.",
            )
        return redirect("assessments:template-detail", pk=template.pk)


class DraftTemplateFormMixin(TemplateSuperAdminMixin):
    template_name = "assessments/templates/form.html"

    def get_template_object(self, pk):
        return get_object_or_404(
            AssessmentTemplate,
            pk=pk,
            publication_status=AssessmentTemplate.PublicationStatus.DRAFT,
        )


class DimensionCreateView(DraftTemplateFormMixin, FormView):
    form_class = DimensionConfigForm

    def dispatch(self, request, *args, **kwargs):
        self.template_object = self.get_template_object(kwargs["template_pk"])
        return super().dispatch(request, *args, **kwargs)

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["template"] = self.template_object
        return kwargs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update(
            page_title="Nueva dimensión",
            template_object=self.template_object,
        )
        return context

    def form_valid(self, form):
        form.save()
        messages.success(self.request, "La dimensión fue agregada al borrador.")
        return redirect("assessments:template-detail", pk=self.template_object.pk)


class DimensionUpdateView(DraftTemplateFormMixin, FormView):
    form_class = DimensionConfigForm

    def dispatch(self, request, *args, **kwargs):
        self.dimension = get_object_or_404(
            Dimension.objects.select_related("template"),
            pk=kwargs["pk"],
        )
        if not self.dimension.template.is_editable:
            raise Http404("La versión publicada es de solo lectura.")
        self.template_object = self.dimension.template
        return super().dispatch(request, *args, **kwargs)

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs.update(template=self.template_object, instance=self.dimension)
        return kwargs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update(
            page_title="Editar dimensión",
            template_object=self.template_object,
        )
        return context

    def form_valid(self, form):
        form.save()
        messages.success(self.request, "La dimensión fue actualizada.")
        return redirect("assessments:template-detail", pk=self.template_object.pk)


class DimensionDeleteView(TemplateSuperAdminMixin, View):
    def post(self, request, pk, *args, **kwargs):
        dimension = get_object_or_404(Dimension.objects.select_related("template"), pk=pk)
        if not dimension.template.is_editable:
            raise Http404("La versión publicada es de solo lectura.")
        template_pk = dimension.template_id
        dimension.delete()
        messages.success(request, "La dimensión fue eliminada del borrador.")
        return redirect("assessments:template-detail", pk=template_pk)


class ScaleQuestionCreateView(DraftTemplateFormMixin, FormView):
    form_class = ScaleQuestionConfigForm

    def dispatch(self, request, *args, **kwargs):
        self.dimension = get_object_or_404(
            Dimension.objects.select_related("template"),
            pk=kwargs["dimension_pk"],
            template__publication_status=AssessmentTemplate.PublicationStatus.DRAFT,
        )
        self.template_object = self.dimension.template
        return super().dispatch(request, *args, **kwargs)

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["dimension"] = self.dimension
        return kwargs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update(
            page_title=f"Nuevo ítem · {self.dimension.name}",
            template_object=self.template_object,
        )
        return context

    def form_valid(self, form):
        form.save()
        messages.success(self.request, "El ítem fue agregado a la dimensión.")
        return redirect("assessments:template-detail", pk=self.template_object.pk)


class ScaleQuestionUpdateView(DraftTemplateFormMixin, FormView):
    form_class = ScaleQuestionConfigForm

    def dispatch(self, request, *args, **kwargs):
        self.question = get_object_or_404(
            Question.objects.select_related("dimension__template"),
            pk=kwargs["pk"],
            dimension__isnull=False,
        )
        self.dimension = self.question.dimension
        if not self.dimension.template.is_editable:
            raise Http404("La versión publicada es de solo lectura.")
        self.template_object = self.dimension.template
        return super().dispatch(request, *args, **kwargs)

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs.update(dimension=self.dimension, instance=self.question)
        return kwargs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update(
            page_title=f"Editar ítem · {self.dimension.name}",
            template_object=self.template_object,
        )
        return context

    def form_valid(self, form):
        form.save()
        messages.success(self.request, "El ítem fue actualizado.")
        return redirect("assessments:template-detail", pk=self.template_object.pk)


class GeneralQuestionCreateView(DraftTemplateFormMixin, FormView):
    form_class = GeneralQuestionConfigForm

    def dispatch(self, request, *args, **kwargs):
        self.template_object = self.get_template_object(kwargs["template_pk"])
        return super().dispatch(request, *args, **kwargs)

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["template"] = self.template_object
        return kwargs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update(
            page_title="Nueva pregunta abierta",
            template_object=self.template_object,
        )
        return context

    def form_valid(self, form):
        form.save()
        messages.success(self.request, "La pregunta abierta fue agregada.")
        return redirect("assessments:template-detail", pk=self.template_object.pk)


class GeneralQuestionUpdateView(DraftTemplateFormMixin, FormView):
    form_class = GeneralQuestionConfigForm

    def dispatch(self, request, *args, **kwargs):
        self.question = get_object_or_404(
            Question.objects.select_related("template"),
            pk=kwargs["pk"],
            dimension__isnull=True,
        )
        self.template_object = self.question.template
        if not self.template_object or not self.template_object.is_editable:
            raise Http404("La versión publicada es de solo lectura.")
        return super().dispatch(request, *args, **kwargs)

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs.update(template=self.template_object, instance=self.question)
        return kwargs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update(
            page_title="Editar pregunta abierta",
            template_object=self.template_object,
        )
        return context

    def form_valid(self, form):
        form.save()
        messages.success(self.request, "La pregunta abierta fue actualizada.")
        return redirect("assessments:template-detail", pk=self.template_object.pk)


class QuestionDeleteView(TemplateSuperAdminMixin, View):
    def post(self, request, pk, *args, **kwargs):
        question = get_object_or_404(Question, pk=pk)
        template = question.assessment_template
        if not template or not template.is_editable:
            raise Http404("La versión publicada es de solo lectura.")
        template_pk = template.pk
        question.delete()
        messages.success(request, "La pregunta fue eliminada del borrador.")
        return redirect("assessments:template-detail", pk=template_pk)
