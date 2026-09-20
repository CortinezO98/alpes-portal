from django.contrib import admin

from .models import (
    DimensionAppreciation,
    IndividualReportVersion,
    OrganizationalReportVersion,
)


@admin.register(DimensionAppreciation)
class DimensionAppreciationAdmin(admin.ModelAdmin):
    list_display = ("assessment", "dimension", "consultant", "updated_at")
    search_fields = ("assessment__participant__email", "dimension__name", "consultant__email")


@admin.register(IndividualReportVersion)
class IndividualReportVersionAdmin(admin.ModelAdmin):
    list_display = ("engagement_participant", "version", "created_by", "created_at")
    list_filter = ("created_at",)
    search_fields = (
        "engagement_participant__participant__email",
        "engagement_participant__engagement__title",
    )
    readonly_fields = ("snapshot", "created_at")


@admin.register(OrganizationalReportVersion)
class OrganizationalReportVersionAdmin(admin.ModelAdmin):
    list_display = ("engagement", "version", "created_by", "created_at")
    list_filter = ("created_at",)
    search_fields = ("engagement__title", "engagement__organization__name")
    readonly_fields = ("snapshot", "created_at")
