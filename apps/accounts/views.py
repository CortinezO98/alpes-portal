from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.views import LoginView, LogoutView
from django.shortcuts import redirect
from django.urls import reverse_lazy
from django.views import View
from django.views.generic import CreateView, ListView, TemplateView

from .forms import EmailAuthenticationForm, UserCreateForm
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
