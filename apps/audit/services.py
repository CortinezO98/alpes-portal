import hashlib
from datetime import timedelta

from django.db import transaction
from django.utils import timezone

from .models import AuditEvent, AuthThrottle


LOGIN_MAX_ATTEMPTS = 5
LOGIN_WINDOW = timedelta(minutes=15)
LOGIN_BLOCK = timedelta(minutes=15)
RESET_MAX_ATTEMPTS = 5
RESET_WINDOW = timedelta(hours=1)
RESET_BLOCK = timedelta(hours=1)


def _hash(value):
    normalized = (value or "").strip().lower().encode("utf-8")
    return hashlib.sha256(normalized).hexdigest()


def request_ip_hash(request):
    return _hash(request.META.get("REMOTE_ADDR", "unknown"))


def identity_hash(value):
    return _hash(value)


def write_audit_event(*, action, request=None, actor=None, target=None, metadata=None):
    target_type = ""
    target_id = ""
    target_label = ""
    if target is not None:
        target_type = target.__class__.__name__
        target_id = str(getattr(target, "pk", ""))
        target_label = str(target)[:255]

    return AuditEvent.objects.create(
        actor=actor,
        action=action,
        target_type=target_type,
        target_id=target_id,
        target_label=target_label,
        ip_hash=request_ip_hash(request) if request is not None else "",
        metadata=metadata or {},
    )


def _policy(scope):
    if scope.startswith("password_reset"):
        return RESET_MAX_ATTEMPTS, RESET_WINDOW, RESET_BLOCK
    return LOGIN_MAX_ATTEMPTS, LOGIN_WINDOW, LOGIN_BLOCK


def is_rate_limited(*, scope, raw_key):
    key_hash = identity_hash(raw_key)
    now = timezone.now()
    throttle = AuthThrottle.objects.filter(scope=scope, key_hash=key_hash).first()
    return bool(throttle and throttle.blocked_until and throttle.blocked_until > now)


def record_attempt(*, scope, raw_key):
    max_attempts, window, block_for = _policy(scope)
    key_hash = identity_hash(raw_key)
    now = timezone.now()

    with transaction.atomic():
        throttle, _ = AuthThrottle.objects.select_for_update().get_or_create(
            scope=scope,
            key_hash=key_hash,
            defaults={"window_started_at": now},
        )

        if now - throttle.window_started_at >= window:
            throttle.window_started_at = now
            throttle.attempts = 0
            throttle.blocked_until = None

        throttle.attempts += 1
        if throttle.attempts >= max_attempts:
            throttle.blocked_until = now + block_for

        throttle.save(
            update_fields=(
                "window_started_at",
                "attempts",
                "blocked_until",
                "updated_at",
            )
        )
        return throttle


def clear_attempts(*, scope, raw_key):
    AuthThrottle.objects.filter(
        scope=scope,
        key_hash=identity_hash(raw_key),
    ).delete()
