from allauth.account.adapter import DefaultAccountAdapter
from allauth.socialaccount.adapter import DefaultSocialAccountAdapter

from .models import User


class AlpesAccountAdapter(DefaultAccountAdapter):
    def save_user(self, request, user, form, commit=True):
        user = super().save_user(request, user, form, commit=False)
        user.role = User.Role.USER
        user.is_staff = False
        user.is_superuser = False
        user.email_verification_required = True
        if commit:
            user.save()
        return user

    def confirm_email(self, request, email_address):
        email_address = super().confirm_email(request, email_address)
        user = email_address.user
        if not user.is_email_verified:
            user.is_email_verified = True
            user.save(update_fields=("is_email_verified",))
        return email_address


class AlpesSocialAccountAdapter(DefaultSocialAccountAdapter):
    def save_user(self, request, sociallogin, form=None):
        user = sociallogin.user
        user.role = User.Role.USER
        user.is_staff = False
        user.is_superuser = False
        user.email_verification_required = True
        user = super().save_user(request, sociallogin, form=form)
        return user
