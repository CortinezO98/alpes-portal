from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.views import LoginView, LogoutView, PasswordResetView
from django.core.exceptions import PermissionDenied
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse_lazy
from django.views import View
from django.views.generic import CreateView, ListView, TemplateView, UpdateView

from apps.audit.models import AuditEvent
from apps.audit.services import (
    clear_attempts,
    is_rate_limited,
    record_attempt,
    write_audit_event,
)

from .forms import EmailAuthenticationForm, UserCreateForm, UserUpdateForm
from .mixins import RoleRequiredMixin
from .models import User


class UserLoginView(LoginView):
    template_name = "accounts/login.html"
    authentication_form = EmailAuthenticationForm
    redirect_authenticated_user = True

    def _rate_keys(self):
        return {
            "login_ip": self.request.META.get("REMOTE_ADDR", "unknown"),
            "login_identity": self.request.POST.get("username", ""),
        }

    def post(self, request, *args, **kwargs):
        keys = self._rate_keys()
        if any(
            is_rate_limited(scope=scope, raw_key=raw_key)
            for scope, raw_key in keys.items()
        ):
            request._login_rate_limited = True
            form = self.get_form()
            form.add_error(
                None,
                "Demasiados intentos. Intenta nuevamente en unos minutos.",
            )
            return self.form_invalid(form)
        return super().post(request, *args, **kwargs)

    def form_invalid(self, form):
        if self.request.method == "POST":
            limited = getattr(self.request, "_login_rate_limited", False)
            if not limited:
                for scope, raw_key in self._rate_keys().items():
                    record_attempt(scope=scope, raw_key=raw_key)
            write_audit_event(
                action=AuditEvent.Action.LOGIN_FAILURE,
                request=self.request,
                metadata={"rate_limited": limited},
            )
        return super().form_invalid(form)

    def form_valid(self, form):
        for scope, raw_key in self._rate_keys().items():
            clear_attempts(scope=scope, raw_key=raw_key)
        response = super().form_valid(form)
        write_audit_event(
            action=AuditEvent.Action.LOGIN_SUCCESS,
            request=self.request,
            actor=self.request.user,
        )
        return response


class UserPasswordResetView(PasswordResetView):
    template_name = "accounts/password_reset_form.html"
    email_template_name = "accounts/password_reset_email.txt"
    subject_template_name = "accounts/password_reset_subject.txt"
    success_url = reverse_lazy("accounts:password-reset-done")

    def post(self, request, *args, **kwargs):
        email = request.POST.get("email", "")
        ip = request.META.get("REMOTE_ADDR", "unknown")
        keys = {
            "password_reset_ip": ip,
            "password_reset_identity": email,
        }
        limited = any(
            is_rate_limited(scope=scope, raw_key=raw_key)
            for scope, raw_key in keys.items()
        )

        for scope, raw_key in keys.items():
            record_attempt(scope=scope, raw_key=raw_key)

        write_audit_event(
            action=AuditEvent.Action.PASSWORD_RESET_REQUEST,
            request=request,
            metadata={"rate_limited": limited},
        )

        if limited:
            return redirect("accounts:password-reset-done")
        return super().post(request, *args, **kwargs)


class UserLogoutView(LogoutView):
    next_page = reverse_lazy("accounts:login")


class DashboardRedirectView(LoginRequiredMixin, View):
    def get(self, request, *args, **kwargs):
        if request.user.is_superuser:
            return redirect("accounts:superadmin-dashboard")

        redirects = {
            User.Role.SUPERADMIN: "accounts:superadmin-dashboard",
            User.Role.ADMIN: "accounts:admin-dashboard",
            User.Role.USER: "accounts:user-dashboard",
        }

        return redirect(
            redirects.get(
                request.user.role,
                "accounts:user-dashboard",
            )
        )


class SuperAdminDashboardView(
    LoginRequiredMixin,
    RoleRequiredMixin,
    TemplateView,
):
    template_name = "accounts/dashboards/superadmin.html"
    allowed_roles = (User.Role.SUPERADMIN,)


class AdminDashboardView(
    LoginRequiredMixin,
    RoleRequiredMixin,
    TemplateView,
):
    template_name = "accounts/dashboards/admin.html"
    allowed_roles = (
        User.Role.ADMIN,
        User.Role.SUPERADMIN,
    )


class UserDashboardView(
    LoginRequiredMixin,
    RoleRequiredMixin,
    TemplateView,
):
    template_name = "accounts/dashboards/user.html"
    allowed_roles = (
        User.Role.USER,
        User.Role.ADMIN,
        User.Role.SUPERADMIN,
    )


class UserManagementListView(
    LoginRequiredMixin,
    RoleRequiredMixin,
    ListView,
):
    template_name = "accounts/users/list.html"
    context_object_name = "users"
    allowed_roles = (User.Role.SUPERADMIN,)
    paginate_by = 20

    def get_queryset(self):
        return User.objects.order_by("email")


class UserManagementCreateView(
    LoginRequiredMixin,
    RoleRequiredMixin,
    CreateView,
):
    template_name = "accounts/users/create.html"
    form_class = UserCreateForm
    success_url = reverse_lazy("accounts:user-management-list")
    allowed_roles = (User.Role.SUPERADMIN,)

    def form_valid(self, form):
        response = super().form_valid(form)
        write_audit_event(
            action=AuditEvent.Action.USER_CREATED,
            request=self.request,
            actor=self.request.user,
            target=self.object,
            metadata={"role": self.object.role},
        )
        messages.success(
            self.request,
            "La cuenta fue creada correctamente.",
        )
        return response


class UserManagementUpdateView(
    LoginRequiredMixin,
    RoleRequiredMixin,
    UpdateView,
):
    template_name = "accounts/users/edit.html"
    form_class = UserUpdateForm
    model = User
    success_url = reverse_lazy("accounts:user-management-list")
    allowed_roles = (User.Role.SUPERADMIN,)

    def get_object(self, queryset=None):
        user = super().get_object(queryset)
        if user.is_superuser or user.role == User.Role.SUPERADMIN:
            raise PermissionDenied
        return user

    def form_valid(self, form):
        previous = User.objects.get(pk=self.object.pk)
        response = super().form_valid(form)
        write_audit_event(
            action=AuditEvent.Action.USER_UPDATED,
            request=self.request,
            actor=self.request.user,
            target=self.object,
            metadata={
                "previous_role": previous.role,
                "new_role": self.object.role,
                "email_changed": previous.email != self.object.email,
            },
        )
        messages.success(
            self.request,
            "La cuenta fue actualizada correctamente.",
        )
        return response


class UserManagementToggleStatusView(
    LoginRequiredMixin,
    RoleRequiredMixin,
    View,
):
    allowed_roles = (User.Role.SUPERADMIN,)

    def post(self, request, pk, *args, **kwargs):
        user = get_object_or_404(User, pk=pk)

        if user.pk == request.user.pk:
            raise PermissionDenied

        if user.is_superuser or user.role == User.Role.SUPERADMIN:
            raise PermissionDenied

        user.is_active = not user.is_active
        user.save(update_fields=("is_active",))

        write_audit_event(
            action=AuditEvent.Action.USER_STATUS_CHANGED,
            request=request,
            actor=request.user,
            target=user,
            metadata={"is_active": user.is_active},
        )

        state = "activada" if user.is_active else "desactivada"
        messages.success(request, f"La cuenta fue {state} correctamente.")
        return redirect("accounts:user-management-list")
