from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db import transaction
from django.shortcuts import get_object_or_404, redirect
from django.views.generic import CreateView, DetailView, FormView, ListView

from apps.accounts.mixins import RoleRequiredMixin
from apps.accounts.models import User
from apps.assessments.models import Assessment

from .forms import (
    EngagementForm,
    EngagementParticipantForm,
    OrganizationForm,
    UnifiedEngagementCreateForm,
)
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


class UnifiedEngagementCreateView(ProgramAdminMixin, FormView):
    template_name = "programs/engagement_create_unified.html"
    form_class = UnifiedEngagementCreateForm

    @transaction.atomic
    def form_valid(self, form):
        cleaned = form.cleaned_data

        organization = cleaned.get("organization")
        if (
            cleaned["mode"] == Engagement.Mode.ORGANIZATIONAL
            and cleaned.get("create_organization")
        ):
            organization = Organization.objects.create(
                name=cleaned["organization_name"].strip(),
                tax_id=(cleaned.get("organization_tax_id") or "").strip(),
                contact_name=(cleaned.get("organization_contact_name") or "").strip(),
                contact_email=(cleaned.get("organization_contact_email") or "").strip(),
            )

        engagement = Engagement(
            title=cleaned["title"].strip(),
            program=cleaned["program"],
            mode=cleaned["mode"],
            organization=organization,
            consultant=self.request.user,
            status=cleaned["status"],
            start_date=cleaned.get("start_date"),
            end_date=cleaned.get("end_date"),
            notes=(cleaned.get("notes") or "").strip(),
        )
        engagement.full_clean()
        engagement.save()

        users = list(cleaned.get("participants") or [])
        created_users = []
        for row in cleaned.get("new_participants_json") or []:
            user = User.objects.create_user(
                email=row["email"],
                password=row["password"],
                first_name=row["first_name"],
                last_name=row["last_name"],
                role=User.Role.USER,
                is_active=True,
            )
            created_users.append(user)
            users.append(user)

        template = cleaned.get("assessment_template")
        assessments_created = 0
        for user in users:
            membership = EngagementParticipant.objects.create(
                engagement=engagement,
                participant=user,
            )
            ensure_participant_phases(membership)

            if cleaned.get("assign_assessment") and template:
                assessment, was_created = Assessment.objects.get_or_create(
                    template=template,
                    participant=user,
                    engagement_participant=membership,
                    defaults={
                        "created_by": self.request.user,
                        "status": Assessment.Status.DRAFT,
                    },
                )
                if was_created:
                    assessments_created += 1

        participant_count = len(users)
        organization_message = (
            f" para {organization.name}" if organization is not None else ""
        )
        messages.success(
            self.request,
            (
                f"Proceso creado correctamente{organization_message}: "
                f"{participant_count} participante(s) vinculados"
                + (
                    f" y {assessments_created} evaluación(es) asignada(s)."
                    if cleaned.get("assign_assessment")
                    else "."
                )
            ),
        )
        return redirect("programs:engagement-detail", pk=engagement.pk)
