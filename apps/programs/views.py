from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import get_object_or_404, redirect
from django.utils import timezone
from django.views import View
from django.views.generic import CreateView, DetailView, FormView, ListView

from apps.accounts.mixins import RoleRequiredMixin
from apps.accounts.models import User

from .forms import (
    EngagementForm,
    EngagementParticipantForm,
    OrganizationForm,
    PhaseArtifactForm,
    PhaseCommentForm,
    UnifiedEngagementCreateForm,
)
from .models import (
    Engagement,
    EngagementParticipant,
    EngagementPhase,
    Organization,
    ParticipantPhase,
    PhaseArtifact,
    PhaseComment,
)
from .services import (
    create_engagement_bundle,
    ensure_participant_phases,
    review_engagement_phase,
    review_participant_phase,
    submit_engagement_phase,
    submit_participant_phase,
)


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
            "phase_progress__phase",
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

    def form_valid(self, form):
        result = create_engagement_bundle(
            cleaned_data=form.cleaned_data,
            actor=self.request.user,
        )
        engagement = result["engagement"]
        organization = result["organization"]
        participant_count = result["participant_count"]
        assessments_created = result["assessments_created"]

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
                    if form.cleaned_data.get("assign_assessment")
                    else "."
                )
            ),
        )
        return redirect("programs:engagement-detail", pk=engagement.pk)


class ParticipantProgressUpdateView(ProgramAdminMixin, View):
    """Allow an administrator to move a participant to a specific program phase."""

    def post(self, request, engagement_pk, participant_pk):
        engagement = get_object_or_404(Engagement, pk=engagement_pk)
        membership = get_object_or_404(
            EngagementParticipant.objects.select_related("participant", "engagement__program"),
            pk=participant_pk,
            engagement=engagement,
        )

        target_progress = get_object_or_404(
            ParticipantPhase.objects.select_related("phase"),
            pk=request.POST.get("phase_progress_id"),
            engagement_participant=membership,
        )

        now = timezone.now()
        progress_items = list(
            membership.phase_progress.select_related("phase").order_by("phase__order", "id")
        )

        for progress in progress_items:
            if progress.phase.order < target_progress.phase.order:
                progress.status = ParticipantPhase.Status.COMPLETED
                progress.started_at = progress.started_at or now
                progress.completed_at = progress.completed_at or now
                progress.completed_by = request.user
            elif progress.pk == target_progress.pk:
                progress.status = ParticipantPhase.Status.IN_PROGRESS
                progress.started_at = progress.started_at or now
                progress.completed_at = None
                progress.completed_by = None
            else:
                progress.status = ParticipantPhase.Status.PENDING
                progress.completed_at = None
                progress.completed_by = None

            progress.save(
                update_fields=(
                    "status",
                    "started_at",
                    "completed_at",
                    "completed_by",
                    "updated_at",
                )
            )

        if engagement.status == Engagement.Status.PLANNING:
            engagement.status = Engagement.Status.ACTIVE
            engagement.save(update_fields=("status", "updated_at"))

        messages.success(
            request,
            (
                f"{membership.participant.email} fue movido a "
                f"“{target_progress.phase.name}”."
            ),
        )
        return redirect("programs:engagement-detail", pk=engagement.pk)


class ParticipantProgressCompleteView(ProgramAdminMixin, View):
    """Mark every phase for a participant as completed."""

    def post(self, request, engagement_pk, participant_pk):
        engagement = get_object_or_404(Engagement, pk=engagement_pk)
        membership = get_object_or_404(
            EngagementParticipant.objects.select_related("participant"),
            pk=participant_pk,
            engagement=engagement,
        )

        now = timezone.now()
        for progress in membership.phase_progress.select_related("phase").all():
            progress.status = ParticipantPhase.Status.COMPLETED
            progress.started_at = progress.started_at or now
            progress.completed_at = progress.completed_at or now
            progress.completed_by = request.user
            progress.save(
                update_fields=(
                    "status",
                    "started_at",
                    "completed_at",
                    "completed_by",
                    "updated_at",
                )
            )

        if engagement.mode == Engagement.Mode.ORGANIZATIONAL:
            report_phase = membership.phase_progress.filter(
                phase__code="reporte-individual"
            ).first()
            if report_phase:
                incomplete_exists = ParticipantPhase.objects.filter(
                    engagement_participant__engagement=engagement,
                    engagement_participant__is_active=True,
                    phase=report_phase.phase,
                ).exclude(status=ParticipantPhase.Status.COMPLETED).exists()
                if not incomplete_exists:
                    engagement.phase_progress.filter(
                        status=ParticipantPhase.Status.PENDING
                    ).update(status=ParticipantPhase.Status.AVAILABLE)

        messages.success(
            request,
            f"El proceso de {membership.participant.email} quedó marcado como completado.",
        )
        return redirect("programs:engagement-detail", pk=engagement.pk)


def _user_is_program_admin(user):
    return bool(
        user.is_authenticated
        and (
            user.is_superuser
            or user.role in {User.Role.ADMIN, User.Role.SUPERADMIN}
        )
    )


def _participant_phase_for_request(request, pk):
    queryset = ParticipantPhase.objects.select_related(
        "phase",
        "engagement_participant__participant",
        "engagement_participant__engagement__program",
        "engagement_participant__engagement__organization",
    ).prefetch_related("artifacts", "comments__author")

    progress = get_object_or_404(queryset, pk=pk)
    is_owner = progress.engagement_participant.participant_id == request.user.id
    if not (_user_is_program_admin(request.user) or is_owner):
        from django.core.exceptions import PermissionDenied
        raise PermissionDenied
    return progress


class ParticipantPhaseDetailView(LoginRequiredMixin, DetailView):
    template_name = "programs/phase_workspace.html"
    context_object_name = "progress"

    def get_queryset(self):
        queryset = ParticipantPhase.objects.select_related(
            "phase",
            "engagement_participant__participant",
            "engagement_participant__engagement__program",
            "engagement_participant__engagement__organization",
        ).prefetch_related("artifacts", "comments__author")
        if _user_is_program_admin(self.request.user):
            return queryset
        return queryset.filter(
            engagement_participant__participant=self.request.user,
            phase__participant_visible=True,
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["artifact_form"] = PhaseArtifactForm()
        context["comment_form"] = PhaseCommentForm()
        context["is_program_admin"] = _user_is_program_admin(self.request.user)
        context["workspace_scope"] = "participant"
        context["engagement"] = self.object.engagement_participant.engagement
        return context


class ParticipantPhaseArtifactCreateView(LoginRequiredMixin, View):
    def post(self, request, pk):
        progress = _participant_phase_for_request(request, pk)
        if not progress.phase.allows_artifacts:
            messages.error(request, "Esta fase no admite soportes.")
            return redirect("programs:participant-phase-detail", pk=progress.pk)

        form = PhaseArtifactForm(request.POST, request.FILES)
        if not form.is_valid():
            messages.error(
                request,
                "No fue posible cargar el soporte. Revisa el formato y el tamaño del archivo.",
            )
            return redirect("programs:participant-phase-detail", pk=progress.pk)

        artifact = form.save(commit=False)
        artifact.participant_phase = progress
        artifact.uploaded_by = request.user
        artifact.original_name = artifact.file.name
        artifact.content_type = getattr(artifact.file, "content_type", "") or ""
        artifact.size_bytes = artifact.file.size
        artifact.save()

        if progress.status in {
            ParticipantPhase.Status.AVAILABLE,
            ParticipantPhase.Status.REOPENED,
        }:
            progress.status = ParticipantPhase.Status.IN_PROGRESS
            progress.started_at = progress.started_at or timezone.now()
            progress.save(update_fields=("status", "started_at", "updated_at"))

        messages.success(request, "El soporte fue cargado correctamente.")
        return redirect("programs:participant-phase-detail", pk=progress.pk)


class ParticipantPhaseCommentCreateView(LoginRequiredMixin, View):
    def post(self, request, pk):
        progress = _participant_phase_for_request(request, pk)
        form = PhaseCommentForm(request.POST)
        if not form.is_valid():
            messages.error(request, "Escribe una apreciación antes de guardarla.")
            return redirect("programs:participant-phase-detail", pk=progress.pk)

        comment = form.save(commit=False)
        comment.participant_phase = progress
        comment.author = request.user
        comment.is_internal = bool(
            _user_is_program_admin(request.user)
            and request.POST.get("is_internal") == "on"
        )
        comment.save()
        messages.success(request, "La apreciación fue registrada.")
        return redirect("programs:participant-phase-detail", pk=progress.pk)


class ParticipantPhaseSubmitView(LoginRequiredMixin, View):
    def post(self, request, pk):
        progress = _participant_phase_for_request(request, pk)
        try:
            submit_participant_phase(progress, request.user)
        except ValueError as exc:
            messages.error(request, str(exc))
        else:
            messages.success(
                request,
                "La fase fue enviada a revisión."
                if progress.phase.requires_review
                else "La fase fue completada.",
            )
        return redirect("programs:participant-phase-detail", pk=progress.pk)


class ParticipantPhaseReviewView(ProgramAdminMixin, View):
    def post(self, request, pk):
        progress = get_object_or_404(
            ParticipantPhase.objects.select_related(
                "phase", "engagement_participant__engagement"
            ),
            pk=pk,
        )
        action = request.POST.get("action")
        note = (request.POST.get("review_note") or "").strip()
        approve = action == "approve"

        if action not in {"approve", "reopen"}:
            messages.error(request, "Acción de revisión no válida.")
            return redirect("programs:participant-phase-detail", pk=progress.pk)

        try:
            review_participant_phase(
                progress,
                actor=request.user,
                approve=approve,
                note=note,
            )
        except ValueError as exc:
            messages.error(request, str(exc))
        else:
            messages.success(
                request,
                "Fase aprobada y hoja de ruta actualizada."
                if approve
                else "La fase fue reabierta para ajustes.",
            )
        return redirect("programs:participant-phase-detail", pk=progress.pk)


class EngagementPhaseDetailView(ProgramAdminMixin, DetailView):
    template_name = "programs/phase_workspace.html"
    context_object_name = "progress"

    def get_queryset(self):
        return EngagementPhase.objects.select_related(
            "phase", "engagement__program", "engagement__organization"
        ).prefetch_related("artifacts", "comments__author")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["artifact_form"] = PhaseArtifactForm()
        context["comment_form"] = PhaseCommentForm()
        context["is_program_admin"] = True
        context["workspace_scope"] = "engagement"
        context["engagement"] = self.object.engagement
        return context


class EngagementPhaseArtifactCreateView(ProgramAdminMixin, View):
    def post(self, request, pk):
        progress = get_object_or_404(
            EngagementPhase.objects.select_related("phase", "engagement"),
            pk=pk,
        )
        form = PhaseArtifactForm(request.POST, request.FILES)
        if not progress.phase.allows_artifacts:
            messages.error(request, "Esta fase no admite soportes.")
        elif form.is_valid():
            artifact = form.save(commit=False)
            artifact.engagement_phase = progress
            artifact.uploaded_by = request.user
            artifact.original_name = artifact.file.name
            artifact.content_type = getattr(artifact.file, "content_type", "") or ""
            artifact.size_bytes = artifact.file.size
            artifact.save()
            if progress.status in {
                ParticipantPhase.Status.AVAILABLE,
                ParticipantPhase.Status.REOPENED,
            }:
                progress.status = ParticipantPhase.Status.IN_PROGRESS
                progress.started_at = progress.started_at or timezone.now()
                progress.save(update_fields=("status", "started_at", "updated_at"))
            messages.success(request, "El soporte organizacional fue cargado.")
        else:
            messages.error(request, "Revisa el formato y el tamaño del archivo.")
        return redirect("programs:engagement-phase-detail", pk=progress.pk)


class EngagementPhaseCommentCreateView(ProgramAdminMixin, View):
    def post(self, request, pk):
        progress = get_object_or_404(EngagementPhase, pk=pk)
        form = PhaseCommentForm(request.POST)
        if form.is_valid():
            comment = form.save(commit=False)
            comment.engagement_phase = progress
            comment.author = request.user
            comment.is_internal = request.POST.get("is_internal") == "on"
            comment.save()
            messages.success(request, "La apreciación organizacional fue registrada.")
        else:
            messages.error(request, "Escribe una apreciación antes de guardarla.")
        return redirect("programs:engagement-phase-detail", pk=progress.pk)


class EngagementPhaseSubmitView(ProgramAdminMixin, View):
    def post(self, request, pk):
        progress = get_object_or_404(
            EngagementPhase.objects.select_related("phase", "engagement"),
            pk=pk,
        )
        try:
            submit_engagement_phase(progress, request.user)
        except ValueError as exc:
            messages.error(request, str(exc))
        else:
            messages.success(
                request,
                "La fase organizacional fue enviada a revisión."
                if progress.phase.requires_review
                else "La fase organizacional fue completada.",
            )
        return redirect("programs:engagement-phase-detail", pk=progress.pk)


class EngagementPhaseReviewView(ProgramAdminMixin, View):
    def post(self, request, pk):
        progress = get_object_or_404(
            EngagementPhase.objects.select_related("phase", "engagement"),
            pk=pk,
        )
        action = request.POST.get("action")
        note = (request.POST.get("review_note") or "").strip()
        if action not in {"approve", "reopen"}:
            messages.error(request, "Acción de revisión no válida.")
            return redirect("programs:engagement-phase-detail", pk=progress.pk)

        try:
            review_engagement_phase(
                progress,
                actor=request.user,
                approve=action == "approve",
                note=note,
            )
        except ValueError as exc:
            messages.error(request, str(exc))
        else:
            messages.success(
                request,
                "Fase organizacional aprobada."
                if action == "approve"
                else "La fase organizacional fue reabierta.",
            )
        return redirect("programs:engagement-phase-detail", pk=progress.pk)
