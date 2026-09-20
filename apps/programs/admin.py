from django.contrib import admin

from .models import (
    Engagement,
    EngagementParticipant,
    EngagementPhase,
    Organization,
    ParticipantPhase,
    PhaseArtifact,
    PhaseComment,
    ProgramPhase,
    ServiceProgram,
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
