from django.contrib import admin

from .models import (
    Engagement,
    EngagementParticipant,
    Organization,
    ParticipantPhase,
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
