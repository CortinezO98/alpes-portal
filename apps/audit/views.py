from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import ListView

from apps.accounts.mixins import RoleRequiredMixin
from apps.accounts.models import User

from .models import AuditEvent


class AuditEventListView(LoginRequiredMixin, RoleRequiredMixin, ListView):
    template_name = "audit/event_list.html"
    context_object_name = "events"
    paginate_by = 50
    allowed_roles = (User.Role.SUPERADMIN,)

    def get_queryset(self):
        queryset = AuditEvent.objects.select_related("actor")
        action = self.request.GET.get("action", "").strip()
        if action in AuditEvent.Action.values:
            queryset = queryset.filter(action=action)
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["action_choices"] = AuditEvent.Action.choices
        context["selected_action"] = self.request.GET.get("action", "")
        return context
