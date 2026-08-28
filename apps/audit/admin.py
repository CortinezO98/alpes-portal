from django.contrib import admin

from .models import AuditEvent


@admin.register(AuditEvent)
class AuditEventAdmin(admin.ModelAdmin):
    list_display = (
        "created_at",
        "action",
        "actor",
        "target_type",
        "target_id",
    )
    list_filter = ("action", "created_at")
    search_fields = ("target_label", "target_id", "actor__email")
    readonly_fields = (
        "actor",
        "action",
        "target_type",
        "target_id",
        "target_label",
        "ip_hash",
        "metadata",
        "created_at",
    )
    ordering = ("-created_at",)

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return request.user.is_superuser

    def has_delete_permission(self, request, obj=None):
        return False
