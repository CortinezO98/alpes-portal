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

    def has_add_permission(self, request):
        return False

    def get_readonly_fields(self, request, obj=None):
        return tuple(field.name for field in self.model._meta.fields)


@admin.register(OrganizationalReportVersion)
class OrganizationalReportVersionAdmin(admin.ModelAdmin):
    list_display = ("engagement", "version", "created_by", "created_at")
    list_filter = ("created_at",)
    search_fields = ("engagement__title", "engagement__organization__name")

    def has_add_permission(self, request):
        return False

    def get_readonly_fields(self, request, obj=None):
        return tuple(field.name for field in self.model._meta.fields)
