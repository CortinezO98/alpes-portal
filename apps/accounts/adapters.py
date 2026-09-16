from allauth.account.adapter import DefaultAccountAdapter
from allauth.socialaccount.adapter import DefaultSocialAccountAdapter

from .models import User


class AlpesAccountAdapter(DefaultAccountAdapter):
    def is_open_for_signup(self, request):
        """Las cuentas se crean únicamente desde la administración de ALPES."""
        return False

    def confirm_email(self, request, email_address):
        email_address = super().confirm_email(request, email_address)
        user = email_address.user
        if not user.is_email_verified:
            user.is_email_verified = True
            user.save(update_fields=("is_email_verified",))
        return email_address


class AlpesSocialAccountAdapter(DefaultSocialAccountAdapter):
    def is_open_for_signup(self, request, sociallogin):
        """Google/Facebook autentican cuentas existentes, nunca crean cuentas."""
        return False

    def is_email_verified(self, provider, email):
        """
        Google conserva la validación propia del proveedor.

        Facebook solo puede usar autenticación por correo cuando ya existe una
        cuenta local activa con ese correo. Esto evita que el flujo social abra
        cuentas nuevas y mantiene el alta bajo control administrativo.
        """
        provider_id = getattr(provider, "id", "")
        if provider_id == "facebook":
            return User.objects.filter(email__iexact=email, is_active=True).exists()
        return super().is_email_verified(provider, email)
