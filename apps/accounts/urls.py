from django.contrib.auth import views as auth_views
from django.urls import path

from .views import (
    AdminDashboardView,
    DashboardRedirectView,
    SuperAdminDashboardView,
    UserDashboardView,
    UserLoginView,
    UserLogoutView,
)


app_name = "accounts"


urlpatterns = [
    path(
        "login/",
        UserLoginView.as_view(),
        name="login",
    ),
    path(
        "logout/",
        UserLogoutView.as_view(),
        name="logout",
    ),
    path(
        "dashboard/",
        DashboardRedirectView.as_view(),
        name="dashboard",
    ),
    path(
        "dashboard/superadmin/",
        SuperAdminDashboardView.as_view(),
        name="superadmin-dashboard",
    ),
    path(
        "dashboard/admin/",
        AdminDashboardView.as_view(),
        name="admin-dashboard",
    ),
    path(
        "dashboard/usuario/",
        UserDashboardView.as_view(),
        name="user-dashboard",
    ),

    path(
        "password/reset/",
        auth_views.PasswordResetView.as_view(
            template_name="accounts/password_reset_form.html",
            email_template_name="accounts/password_reset_email.txt",
            subject_template_name="accounts/password_reset_subject.txt",
            success_url="/cuenta/password/reset/enviado/",
        ),
        name="password-reset",
    ),
    path(
        "password/reset/enviado/",
        auth_views.PasswordResetDoneView.as_view(
            template_name="accounts/password_reset_done.html",
        ),
        name="password-reset-done",
    ),
    path(
        "password/reset/<uidb64>/<token>/",
        auth_views.PasswordResetConfirmView.as_view(
            template_name="accounts/password_reset_confirm.html",
            success_url="/cuenta/password/reset/completado/",
        ),
        name="password-reset-confirm",
    ),
    path(
        "password/reset/completado/",
        auth_views.PasswordResetCompleteView.as_view(
            template_name="accounts/password_reset_complete.html",
        ),
        name="password-reset-complete",
    ),
]