from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import get_object_or_404, redirect
from django.views.generic import CreateView, DetailView, ListView

from apps.accounts.mixins import RoleRequiredMixin
from apps.accounts.models import User

from .forms import EngagementForm, EngagementParticipantForm, OrganizationForm
from .models import Engagement, EngagementParticipant, Organization
from .services import ensure_participant_phases


class ProgramAdminMixin(LoginRequiredMixin, RoleRequiredMixin):
    allowed_roles = (User.Role.ADMIN, User.Role.SUPERADMIN)


class EngagementListView(ProgramAdminMixin, ListView):
    template_name = "programs/engagement_list.html"
    context_object_name = "engagements"
    paginate_by = 20

    def get_queryset(self):
        return Engagement.objects.select_related(
            "program", "organization", "consultant"
        ).prefetch_related("participants").order_by("-created_at")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["organizations"] = Organization.objects.filter(is_active=True).order_by("name")
        return context


class OrganizationCreateView(ProgramAdminMixin, CreateView):
    template_name = "programs/organization_form.html"
    form_class = OrganizationForm

    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(self.request, "La organización fue creada correctamente.")
        return response

    def get_success_url(self):
        return "/programas/"


class EngagementCreateView(ProgramAdminMixin, CreateView):
    template_name = "programs/engagement_form.html"
    form_class = EngagementForm

    def form_valid(self, form):
        engagement = form.save(commit=False)
        engagement.consultant = self.request.user
        engagement.full_clean()
        engagement.save()
        self.object = engagement
        messages.success(self.request, "El proceso de acompañamiento fue creado.")
        return redirect("programs:engagement-detail", pk=engagement.pk)


class EngagementDetailView(ProgramAdminMixin, DetailView):
    template_name = "programs/engagement_detail.html"
    context_object_name = "engagement"

    def get_queryset(self):
        return Engagement.objects.select_related(
            "program", "organization", "consultant"
        ).prefetch_related(
            "program__phases",
            "participants__participant",
            "participants__phase_progress__phase",
        )


class EngagementParticipantCreateView(ProgramAdminMixin, CreateView):
    template_name = "programs/participant_form.html"
    form_class = EngagementParticipantForm

    def dispatch(self, request, *args, **kwargs):
        self.engagement = get_object_or_404(Engagement, pk=kwargs["pk"])
        return super().dispatch(request, *args, **kwargs)

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["engagement"] = self.engagement
        return kwargs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["engagement"] = self.engagement
        return context

    def form_valid(self, form):
        participant = form.save()
        ensure_participant_phases(participant)
        messages.success(self.request, "El participante fue vinculado al proceso.")
        return redirect("programs:engagement-detail", pk=self.engagement.pk)


class MyEngagementListView(LoginRequiredMixin, ListView):
    template_name = "programs/my_engagements.html"
    context_object_name = "participations"

    def get_queryset(self):
        return EngagementParticipant.objects.filter(
            participant=self.request.user,
            is_active=True,
        ).select_related(
            "engagement__program",
            "engagement__organization",
        ).prefetch_related("phase_progress__phase").order_by("-engagement__created_at")


class MyEngagementDetailView(LoginRequiredMixin, DetailView):
    template_name = "programs/my_engagement_detail.html"
    context_object_name = "participation"

    def get_queryset(self):
        return EngagementParticipant.objects.filter(
            participant=self.request.user,
            is_active=True,
        ).select_related(
            "engagement__program",
            "engagement__organization",
        ).prefetch_related(
            "phase_progress__phase",
            "assessments__template",
        )
