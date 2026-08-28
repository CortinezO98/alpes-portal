from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.views import LoginView, LogoutView
from django.core.exceptions import PermissionDenied
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse_lazy
from django.views import View
from django.views.generic import CreateView, ListView, TemplateView, UpdateView

from .forms import EmailAuthenticationForm, UserCreateForm, UserUpdateForm
from .mixins import RoleRequiredMixin
from .models import User


class UserLoginView(LoginView):
    template_name = "accounts/login.html"
    authentication_form = EmailAuthenticationForm
    redirect_authenticated_user = True


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
        response = super().form_valid(form)
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

        state = "activada" if user.is_active else "desactivada"
        messages.success(request, f"La cuenta fue {state} correctamente.")
        return redirect("accounts:user-management-list")
