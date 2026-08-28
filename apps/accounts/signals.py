from allauth.account.signals import email_confirmed, user_signed_up
from django.dispatch import receiver

from apps.audit.models import AuditEvent
from apps.audit.services import write_audit_event


@receiver(user_signed_up)
def audit_public_signup(request, user, **kwargs):
    write_audit_event(
        action=AuditEvent.Action.USER_CREATED,
        request=request,
        target=user,
        metadata={"role": user.role, "source": "public_signup"},
    )


@receiver(email_confirmed)
def sync_verified_email_flag(request, email_address, **kwargs):
    user = email_address.user
    if not user.is_email_verified:
        user.is_email_verified = True
        user.save(update_fields=("is_email_verified",))
