from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import get_object_or_404, redirect
from django.utils import timezone
from django.views import View
from django.views.generic import CreateView, DetailView, FormView, ListView

from apps.accounts.mixins import RoleRequiredMixin
from apps.accounts.models import User

from .forms import (
    ActionPlanGoalForm,
    ActionPlanItemForm,
    ConsultantExperienceRecordForm,
    DreamChallengeNodeForm,
    EngagementForm,
    EngagementParticipantForm,
    OrganizationForm,
    PhaseArtifactForm,
    PhaseCommentForm,
    TransformationSessionForm,
    UnifiedEngagementCreateForm,
)
from .models import (
    ActionPlanGoal,
    ActionPlanItem,
    ConsultantExperienceRecord,
    DreamChallengeNode,
    Engagement,
    EngagementParticipant,
    EngagementPhase,
    Organization,
    ParticipantPhase,
    PhaseComment,
    TransformationSession,
)
from .services import (
    create_engagement_bundle,
    ensure_participant_phases,
    reconcile_participation_assessment,
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

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        participants = list(self.object.participants.all())
        participant_count = len(participants)
        progress_values = [item.progress_percent for item in participants]
        average_progress = (
            round(sum(progress_values) / participant_count)
            if participant_count
            else 0
        )

        phase_items = [
            progress
            for participant in participants
            for progress in participant.phase_progress.all()
        ]
        review_count = sum(
            1
            for progress in phase_items
            if progress.status
            in {
                ParticipantPhase.Status.SUBMITTED,
                ParticipantPhase.Status.UNDER_REVIEW,
            }
        )
        reopened_count = sum(
            1
            for progress in phase_items
            if progress.status == ParticipantPhase.Status.REOPENED
        )
        completed_count = sum(
            1
            for participant in participants
            if participant.progress_percent == 100
        )

        context.update(
            participant_count=participant_count,
            average_progress=average_progress,
            review_count=review_count,
            reopened_count=reopened_count,
            completed_participant_count=completed_count,
            participant_phases=self.object.program.phases.filter(
                scope="PARTICIPANT"
            ).order_by("order", "id"),
        )
        return context


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

        reason = (request.POST.get("manual_reason") or "").strip()
        if not reason:
            messages.error(
                request,
                "Indica el motivo del ajuste manual para conservar la trazabilidad.",
            )
            return redirect("programs:engagement-detail", pk=engagement.pk)

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

        PhaseComment.objects.create(
            participant_phase=target_progress,
            author=request.user,
            body=(
                f"Ajuste manual de hoja de ruta. Nueva fase actual: "
                f"{target_progress.phase.name}. Motivo: {reason}"
            ),
            is_internal=True,
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

    def get_object(self, queryset=None):
        obj = super().get_object(queryset)
        self.assessment_reconciliation = None
        if obj.phase.code == "rueda-vida":
            result = reconcile_participation_assessment(
                obj.engagement_participant,
                actor=self.request.user if _user_is_program_admin(self.request.user) else None,
            )
            if result["status"] in {"linked_completed", "synchronized_completed"}:
                obj.refresh_from_db()
            self.assessment_reconciliation = result
        return obj

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["artifact_form"] = PhaseArtifactForm()
        context["comment_form"] = PhaseCommentForm()
        context["is_program_admin"] = _user_is_program_admin(self.request.user)
        context["workspace_scope"] = "participant"
        context["engagement"] = self.object.engagement_participant.engagement
        context["assessment_reconciliation"] = self.assessment_reconciliation

        if self.object.phase.code == "charla-inicial":
            record = getattr(self.object, "consultant_experience", None)
            context["consultant_experience_record"] = record
            if context["is_program_admin"]:
                context["consultant_experience_form"] = ConsultantExperienceRecordForm(
                    instance=record
                )
        elif self.object.phase.code == "conversaciones":
            context["transformation_form"] = TransformationSessionForm()
            context["transformation_sessions"] = self.object.transformation_sessions.all()
        elif self.object.phase.code == "mapa-retos-suenos":
            context["dream_node_form"] = DreamChallengeNodeForm(
                participant_phase=self.object
            )
            dream_nodes = list(
                self.object.dream_map_nodes.select_related("parent").prefetch_related(
                    "linked_action_goals__items"
                ).all()
            )
            context["dream_nodes"] = dream_nodes
            context["dream_map_graph"] = [
                {
                    "id": node.pk,
                    "parent_id": node.parent_id,
                    "title": node.title,
                    "description": node.description,
                    "type": node.node_type,
                    "type_label": node.get_node_type_display(),
                    "priority": node.priority,
                    "priority_label": node.get_priority_display(),
                    "target_date": (
                        node.target_date.strftime("%d/%m/%Y")
                        if node.target_date
                        else ""
                    ),
                    "goals": [
                        {
                            "id": goal.pk,
                            "title": goal.title,
                            "description": goal.description,
                            "target_date": (
                                goal.target_date.strftime("%d/%m/%Y")
                                if goal.target_date
                                else ""
                            ),
                            "items": [
                                {
                                    "id": item.pk,
                                    "action": item.action,
                                    "indicator": item.indicator,
                                    "responsible": item.responsible,
                                    "due_date": (
                                        item.due_date.strftime("%d/%m/%Y")
                                        if item.due_date
                                        else ""
                                    ),
                                    "status": item.status,
                                    "status_label": item.get_status_display(),
                                    "consultant_appreciation": item.consultant_appreciation,
                                }
                                for item in goal.items.all()
                            ],
                        }
                        for goal in node.linked_action_goals.all()
                    ],
                }
                for node in dream_nodes
            ]
        elif self.object.phase.code == "plan-accion":
            context["action_goal_form"] = ActionPlanGoalForm()
            context["action_item_form"] = ActionPlanItemForm()
            action_goals = self.object.action_goals.select_related("source_node").prefetch_related("items").all()
            context["action_goals"] = action_goals

            map_progress = (
                self.object.engagement_participant.phase_progress.filter(
                    phase__code="mapa-retos-suenos"
                )
                .select_related("phase")
                .first()
            )
            existing_goal_keys = {
                (
                    goal.title.strip().lower(),
                    (goal.description or "").strip().lower(),
                    goal.target_date,
                )
                for goal in action_goals
            }
            context["dream_map_options"] = []
            context["dream_map_pending_count"] = 0
            if map_progress:
                nodes = list(
                    map_progress.dream_map_nodes.select_related("parent").all()
                )
                by_id = {node.pk: node for node in nodes}

                def node_path(node):
                    labels = [node.title]
                    seen = {node.pk}
                    parent = node.parent
                    while parent and parent.pk not in seen:
                        seen.add(parent.pk)
                        labels.append(parent.title)
                        parent = by_id.get(parent.parent_id)
                    labels.reverse()
                    return " → ".join(labels)

                options = []
                for node in nodes:
                    already_added = (
                        self.object.action_goals.filter(source_node=node).exists()
                        or (
                            node.title.strip().lower(),
                            (node.description or "").strip().lower(),
                            node.target_date,
                        )
                        in existing_goal_keys
                    )
                    options.append(
                        {
                            "node": node,
                            "already_added": already_added,
                            "path": node_path(node),
                        }
                    )
                context["dream_map_options"] = options
                context["dream_map_pending_count"] = sum(
                    1 for option in options if not option["already_added"]
                )

        return context


class ConsultantExperienceSaveView(ProgramAdminMixin, View):
    def post(self, request, pk):
        progress = get_object_or_404(
            ParticipantPhase.objects.select_related(
                "phase",
                "engagement_participant__engagement",
            ),
            pk=pk,
        )
        if progress.phase.code != "charla-inicial":
            messages.error(request, "Esta fase no corresponde a la charla inicial.")
            return redirect("programs:participant-phase-detail", pk=progress.pk)

        if progress.status in {
            ParticipantPhase.Status.PENDING,
            ParticipantPhase.Status.COMPLETED,
            ParticipantPhase.Status.SUBMITTED,
            ParticipantPhase.Status.UNDER_REVIEW,
        }:
            messages.error(request, "La charla no puede editarse en el estado actual de la fase.")
            return redirect("programs:participant-phase-detail", pk=progress.pk)

        record = ConsultantExperienceRecord.objects.filter(
            participant_phase=progress
        ).first()
        form = ConsultantExperienceRecordForm(request.POST, instance=record)
        if not form.is_valid():
            messages.error(request, "Revisa la información de la charla y vuelve a intentarlo.")
            return redirect("programs:participant-phase-detail", pk=progress.pk)

        saved = form.save(commit=False)
        saved.participant_phase = progress
        if record is None:
            saved.created_by = request.user
        saved.updated_by = request.user
        saved.save()

        _mark_phase_in_progress(progress)
        messages.success(request, "La charla y experiencia del consultor fue guardada.")
        return redirect("programs:participant-phase-detail", pk=progress.pk)


class ParticipantPhaseArtifactCreateView(LoginRequiredMixin, View):
    def post(self, request, pk):
        progress = _participant_phase_for_request(request, pk)
        if not progress.phase.allows_artifacts:
            messages.error(request, "Esta fase no admite soportes.")
            return redirect("programs:participant-phase-detail", pk=progress.pk)
        if progress.status in {
            ParticipantPhase.Status.PENDING,
            ParticipantPhase.Status.COMPLETED,
            ParticipantPhase.Status.SUBMITTED,
            ParticipantPhase.Status.UNDER_REVIEW,
        }:
            messages.error(request, "La fase no está disponible para cargar soportes.")
            return redirect("programs:participant-phase-detail", pk=progress.pk)

        form = PhaseArtifactForm(request.POST, request.FILES)
        if not form.is_valid():
            messages.error(
                request,
                "No fue posible cargar el soporte. Revisa el formato y el tamaño del archivo.",
            )
            return redirect("programs:participant-phase-detail", pk=progress.pk)

        uploaded_file = form.cleaned_data["file"]
        artifact = form.save(commit=False)
        artifact.participant_phase = progress
        artifact.uploaded_by = request.user
        artifact.original_name = uploaded_file.name
        artifact.content_type = getattr(uploaded_file, "content_type", "") or ""
        artifact.size_bytes = uploaded_file.size
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
        if progress.status in {
            ParticipantPhase.Status.PENDING,
            ParticipantPhase.Status.COMPLETED,
        }:
            messages.error(request, "La fase no está disponible para nuevas apreciaciones.")
            return redirect("programs:participant-phase-detail", pk=progress.pk)
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
            uploaded_file = form.cleaned_data["file"]
            artifact = form.save(commit=False)
            artifact.engagement_phase = progress
            artifact.uploaded_by = request.user
            artifact.original_name = uploaded_file.name
            artifact.content_type = getattr(uploaded_file, "content_type", "") or ""
            artifact.size_bytes = uploaded_file.size
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



class RoadmapDetailView(LoginRequiredMixin, DetailView):
    template_name = "programs/roadmap_detail.html"
    context_object_name = "participation"

    def get_queryset(self):
        queryset = EngagementParticipant.objects.select_related(
            "participant",
            "engagement__program",
            "engagement__organization",
            "engagement__consultant",
        ).prefetch_related(
            "phase_progress__phase",
            "phase_progress__artifacts",
            "phase_progress__comments__author",
            "phase_progress__consultant_experience",
            "phase_progress__transformation_sessions",
            "phase_progress__dream_map_nodes__parent",
            "phase_progress__action_goals__items",
        )
        if _user_is_program_admin(self.request.user):
            return queryset
        return queryset.filter(participant=self.request.user, is_active=True)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["is_program_admin"] = _user_is_program_admin(self.request.user)
        return context



def _mark_phase_in_progress(progress):
    if progress.status in {
        ParticipantPhase.Status.AVAILABLE,
        ParticipantPhase.Status.REOPENED,
    }:
        progress.status = ParticipantPhase.Status.IN_PROGRESS
        progress.started_at = progress.started_at or timezone.now()
        progress.save(update_fields=("status", "started_at", "updated_at"))


class TransformationSessionCreateView(LoginRequiredMixin, View):
    def post(self, request, pk):
        progress = _participant_phase_for_request(request, pk)
        if progress.phase.code != "conversaciones":
            messages.error(request, "Esta fase no admite sesiones transformadoras.")
            return redirect("programs:participant-phase-detail", pk=progress.pk)
        if progress.status in {
            ParticipantPhase.Status.PENDING,
            ParticipantPhase.Status.COMPLETED,
            ParticipantPhase.Status.SUBMITTED,
            ParticipantPhase.Status.UNDER_REVIEW,
        }:
            messages.error(request, "La fase no está disponible para edición.")
            return redirect("programs:participant-phase-detail", pk=progress.pk)

        form = TransformationSessionForm(request.POST)
        if not form.is_valid():
            messages.error(request, "Revisa la información de la sesión.")
            return redirect("programs:participant-phase-detail", pk=progress.pk)

        session = form.save(commit=False)
        session.participant_phase = progress
        session.created_by = request.user
        if not _user_is_program_admin(request.user):
            session.consultant_appreciation = ""
        session.save()
        _mark_phase_in_progress(progress)
        messages.success(request, "La conversación transformadora fue registrada.")
        return redirect("programs:participant-phase-detail", pk=progress.pk)


class DreamChallengeNodeCreateView(LoginRequiredMixin, View):
    def post(self, request, pk):
        progress = _participant_phase_for_request(request, pk)
        if progress.phase.code != "mapa-retos-suenos":
            messages.error(request, "Esta fase no admite elementos del mapa.")
            return redirect("programs:participant-phase-detail", pk=progress.pk)
        if progress.status in {
            ParticipantPhase.Status.PENDING,
            ParticipantPhase.Status.COMPLETED,
            ParticipantPhase.Status.SUBMITTED,
            ParticipantPhase.Status.UNDER_REVIEW,
        }:
            messages.error(request, "La fase no está disponible para edición.")
            return redirect("programs:participant-phase-detail", pk=progress.pk)

        form = DreamChallengeNodeForm(request.POST, participant_phase=progress)
        if not form.is_valid():
            messages.error(request, "Revisa la información del elemento del mapa.")
            return redirect("programs:participant-phase-detail", pk=progress.pk)

        node = form.save(commit=False)
        node.participant_phase = progress
        node.created_by = request.user
        node.order = progress.dream_map_nodes.count() + 1
        node.save()
        _mark_phase_in_progress(progress)
        messages.success(request, f"{node.get_node_type_display()} agregado al mapa.")
        return redirect("programs:participant-phase-detail", pk=progress.pk)


class ActionPlanGoalImportFromMapView(LoginRequiredMixin, View):
    def post(self, request, pk, node_pk):
        progress = _participant_phase_for_request(request, pk)
        if progress.phase.code != "plan-accion":
            messages.error(request, "Esta fase no admite metas del plan de acción.")
            return redirect("programs:participant-phase-detail", pk=progress.pk)
        if progress.status in {
            ParticipantPhase.Status.PENDING,
            ParticipantPhase.Status.COMPLETED,
            ParticipantPhase.Status.SUBMITTED,
            ParticipantPhase.Status.UNDER_REVIEW,
        }:
            messages.error(request, "La fase no está disponible para edición.")
            return redirect("programs:participant-phase-detail", pk=progress.pk)

        map_progress = get_object_or_404(
            ParticipantPhase.objects.select_related("phase"),
            engagement_participant=progress.engagement_participant,
            phase__code="mapa-retos-suenos",
        )
        node = get_object_or_404(
            DreamChallengeNode,
            pk=node_pk,
            participant_phase=map_progress,
        )

        duplicate = progress.action_goals.filter(source_node=node).exists()
        if not duplicate:
            duplicate = progress.action_goals.filter(
                title__iexact=node.title.strip(),
                description=node.description or "",
                target_date=node.target_date,
            ).exists()
        if duplicate:
            messages.info(request, "Este elemento del mapa ya fue agregado al plan de acción.")
            return redirect("programs:participant-phase-detail", pk=progress.pk)

        ActionPlanGoal.objects.create(
            participant_phase=progress,
            source_node=node,
            title=node.title,
            description=node.description,
            target_date=node.target_date,
            order=progress.action_goals.count() + 1,
            created_by=request.user,
        )
        _mark_phase_in_progress(progress)
        messages.success(
            request,
            f"“{node.title}” fue agregado al plan de acción desde el mapa.",
        )
        return redirect("programs:participant-phase-detail", pk=progress.pk)


class ActionPlanGoalCreateView(LoginRequiredMixin, View):
    def post(self, request, pk):
        progress = _participant_phase_for_request(request, pk)
        if progress.phase.code != "plan-accion":
            messages.error(request, "Esta fase no admite metas del plan de acción.")
            return redirect("programs:participant-phase-detail", pk=progress.pk)
        if progress.status in {
            ParticipantPhase.Status.PENDING,
            ParticipantPhase.Status.COMPLETED,
            ParticipantPhase.Status.SUBMITTED,
            ParticipantPhase.Status.UNDER_REVIEW,
        }:
            messages.error(request, "La fase no está disponible para edición.")
            return redirect("programs:participant-phase-detail", pk=progress.pk)

        form = ActionPlanGoalForm(request.POST)
        if not form.is_valid():
            messages.error(request, "Revisa la información de la meta.")
            return redirect("programs:participant-phase-detail", pk=progress.pk)

        goal = form.save(commit=False)
        goal.participant_phase = progress
        goal.created_by = request.user
        goal.order = progress.action_goals.count() + 1
        goal.save()
        _mark_phase_in_progress(progress)
        messages.success(request, "La meta fue agregada al plan de acción.")
        return redirect("programs:participant-phase-detail", pk=progress.pk)


class ActionPlanItemCreateView(LoginRequiredMixin, View):
    def post(self, request, pk, goal_pk):
        progress = _participant_phase_for_request(request, pk)
        goal = get_object_or_404(
            ActionPlanGoal,
            pk=goal_pk,
            participant_phase=progress,
        )
        if progress.phase.code != "plan-accion":
            messages.error(request, "Esta fase no admite acciones.")
            return redirect("programs:participant-phase-detail", pk=progress.pk)
        if progress.status in {
            ParticipantPhase.Status.PENDING,
            ParticipantPhase.Status.COMPLETED,
            ParticipantPhase.Status.SUBMITTED,
            ParticipantPhase.Status.UNDER_REVIEW,
        }:
            messages.error(request, "La fase no está disponible para edición.")
            return redirect("programs:participant-phase-detail", pk=progress.pk)

        form = ActionPlanItemForm(request.POST)
        if not form.is_valid():
            messages.error(request, "Revisa la información de la acción.")
            return redirect("programs:participant-phase-detail", pk=progress.pk)

        item = form.save(commit=False)
        item.goal = goal
        item.created_by = request.user
        item.order = goal.items.count() + 1
        if not _user_is_program_admin(request.user):
            item.consultant_appreciation = ""
        item.save()
        _mark_phase_in_progress(progress)
        messages.success(request, "La acción fue agregada a la meta.")
        return redirect("programs:participant-phase-detail", pk=progress.pk)


class ActionPlanItemUpdateView(LoginRequiredMixin, View):
    def post(self, request, pk, item_pk):
        progress = _participant_phase_for_request(request, pk)
        item = get_object_or_404(
            ActionPlanItem.objects.select_related("goal"),
            pk=item_pk,
            goal__participant_phase=progress,
        )
        if progress.status in {
            ParticipantPhase.Status.PENDING,
            ParticipantPhase.Status.COMPLETED,
            ParticipantPhase.Status.SUBMITTED,
            ParticipantPhase.Status.UNDER_REVIEW,
        }:
            messages.error(request, "La fase no está disponible para edición.")
            return redirect("programs:participant-phase-detail", pk=progress.pk)

        previous_appreciation = item.consultant_appreciation
        form = ActionPlanItemForm(request.POST, instance=item)
        if not form.is_valid():
            messages.error(request, "No fue posible actualizar la acción.")
            return redirect("programs:participant-phase-detail", pk=progress.pk)

        updated = form.save(commit=False)
        if not _user_is_program_admin(request.user):
            updated.consultant_appreciation = previous_appreciation
        updated.save()
        _mark_phase_in_progress(progress)
        messages.success(request, "La acción fue actualizada.")
        return redirect("programs:participant-phase-detail", pk=progress.pk)



class TransformationSessionUpdateView(LoginRequiredMixin, View):
    def post(self, request, pk, session_pk):
        progress = _participant_phase_for_request(request, pk)
        session = get_object_or_404(
            TransformationSession,
            pk=session_pk,
            participant_phase=progress,
        )
        if progress.status in {
            ParticipantPhase.Status.PENDING,
            ParticipantPhase.Status.COMPLETED,
            ParticipantPhase.Status.SUBMITTED,
            ParticipantPhase.Status.UNDER_REVIEW,
        }:
            messages.error(request, "La sesión no puede editarse en el estado actual de la fase.")
            return redirect("programs:participant-phase-detail", pk=progress.pk)

        previous_appreciation = session.consultant_appreciation
        form = TransformationSessionForm(request.POST, instance=session)
        if not form.is_valid():
            messages.error(request, "Revisa la información de la sesión.")
            return redirect("programs:participant-phase-detail", pk=progress.pk)

        updated = form.save(commit=False)
        if not _user_is_program_admin(request.user):
            updated.consultant_appreciation = previous_appreciation
        updated.save()
        _mark_phase_in_progress(progress)
        messages.success(request, "La sesión fue actualizada.")
        return redirect("programs:participant-phase-detail", pk=progress.pk)


class DreamChallengeNodeUpdateView(LoginRequiredMixin, View):
    def post(self, request, pk, node_pk):
        progress = _participant_phase_for_request(request, pk)
        node = get_object_or_404(
            DreamChallengeNode,
            pk=node_pk,
            participant_phase=progress,
        )
        if progress.status in {
            ParticipantPhase.Status.PENDING,
            ParticipantPhase.Status.COMPLETED,
            ParticipantPhase.Status.SUBMITTED,
            ParticipantPhase.Status.UNDER_REVIEW,
        }:
            messages.error(request, "El mapa no puede editarse en el estado actual de la fase.")
            return redirect("programs:participant-phase-detail", pk=progress.pk)

        form = DreamChallengeNodeForm(
            request.POST,
            instance=node,
            participant_phase=progress,
        )
        form.fields["parent"].queryset = form.fields["parent"].queryset.exclude(pk=node.pk)
        if not form.is_valid():
            messages.error(request, "Revisa la información del elemento del mapa.")
            return redirect("programs:participant-phase-detail", pk=progress.pk)

        form.save()
        _mark_phase_in_progress(progress)
        messages.success(request, "El elemento del mapa fue actualizado.")
        return redirect("programs:participant-phase-detail", pk=progress.pk)


class ActionPlanGoalUpdateView(LoginRequiredMixin, View):
    def post(self, request, pk, goal_pk):
        progress = _participant_phase_for_request(request, pk)
        goal = get_object_or_404(
            ActionPlanGoal,
            pk=goal_pk,
            participant_phase=progress,
        )
        if progress.status in {
            ParticipantPhase.Status.PENDING,
            ParticipantPhase.Status.COMPLETED,
            ParticipantPhase.Status.SUBMITTED,
            ParticipantPhase.Status.UNDER_REVIEW,
        }:
            messages.error(request, "La meta no puede editarse en el estado actual de la fase.")
            return redirect("programs:participant-phase-detail", pk=progress.pk)

        form = ActionPlanGoalForm(request.POST, instance=goal)
        if not form.is_valid():
            messages.error(request, "Revisa la información de la meta.")
            return redirect("programs:participant-phase-detail", pk=progress.pk)

        form.save()
        _mark_phase_in_progress(progress)
        messages.success(request, "La meta fue actualizada.")
        return redirect("programs:participant-phase-detail", pk=progress.pk)
