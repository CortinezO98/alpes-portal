from django.contrib import admin

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
    PhaseArtifact,
    PhaseComment,
    ProgramPhase,
    ServiceProgram,
    TransformationSession,
)


@admin.register(Organization)
class OrganizationAdmin(admin.ModelAdmin):
    list_display = ("name", "tax_id", "city", "is_active")
    search_fields = ("name", "tax_id", "contact_email")
    list_filter = ("is_active",)


class ProgramPhaseInline(admin.TabularInline):
    model = ProgramPhase
    extra = 0
    ordering = ("order",)


@admin.register(ServiceProgram)
class ServiceProgramAdmin(admin.ModelAdmin):
    list_display = ("name", "code", "is_active")
    inlines = (ProgramPhaseInline,)


@admin.register(Engagement)
class EngagementAdmin(admin.ModelAdmin):
    list_display = ("title", "program", "mode", "organization", "status", "consultant")
    list_filter = ("mode", "status", "program")
    search_fields = ("title", "organization__name")


@admin.register(EngagementParticipant)
class EngagementParticipantAdmin(admin.ModelAdmin):
    list_display = ("engagement", "participant", "is_active", "joined_at")
    search_fields = ("participant__email", "engagement__title")


@admin.register(ParticipantPhase)
class ParticipantPhaseAdmin(admin.ModelAdmin):
    list_display = ("engagement_participant", "phase", "status", "completed_at")
    list_filter = ("status", "phase__program")



@admin.register(EngagementPhase)
class EngagementPhaseAdmin(admin.ModelAdmin):
    list_display = ("engagement", "phase", "status", "completed_at")
    list_filter = ("status", "phase__program")


@admin.register(PhaseArtifact)
class PhaseArtifactAdmin(admin.ModelAdmin):
    list_display = ("original_name", "uploaded_by", "created_at")
    search_fields = ("original_name", "uploaded_by__email")


@admin.register(PhaseComment)
class PhaseCommentAdmin(admin.ModelAdmin):
    list_display = ("author", "is_internal", "created_at")
    list_filter = ("is_internal",)



@admin.register(TransformationSession)
class TransformationSessionAdmin(admin.ModelAdmin):
    list_display = ("session_date", "title", "participant_phase", "created_by")
    search_fields = ("title", "participant_phase__engagement_participant__participant__email")


@admin.register(DreamChallengeNode)
class DreamChallengeNodeAdmin(admin.ModelAdmin):
    list_display = ("title", "node_type", "priority", "participant_phase", "target_date")
    list_filter = ("node_type", "priority")


class ActionPlanItemInline(admin.TabularInline):
    model = ActionPlanItem
    extra = 0


@admin.register(ActionPlanGoal)
class ActionPlanGoalAdmin(admin.ModelAdmin):
    list_display = ("title", "participant_phase", "target_date")
    inlines = (ActionPlanItemInline,)


@admin.register(ActionPlanItem)
class ActionPlanItemAdmin(admin.ModelAdmin):
    list_display = ("action", "goal", "status", "due_date")
    list_filter = ("status",)



@admin.register(ConsultantExperienceRecord)
class ConsultantExperienceRecordAdmin(admin.ModelAdmin):
    list_display = ("session_date", "topic", "participant_phase", "updated_by", "updated_at")
    search_fields = (
        "topic",
        "participant_phase__engagement_participant__participant__email",
    )
