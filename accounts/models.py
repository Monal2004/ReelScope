import secrets
from datetime import timedelta

from django.conf import settings
from django.db import models
from django.utils import timezone

VERIFICATION_TOKEN_BYTES = 32


def generate_token():
    return secrets.token_urlsafe(VERIFICATION_TOKEN_BYTES)


def default_expiry():
    return timezone.now() + timedelta(hours=settings.EMAIL_VERIFICATION_HOURS)


class EmailVerification(models.Model):
    """A one-time, expiring token that activates a registered account."""

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="email_verification",
    )
    token = models.CharField(max_length=64, unique=True, default=generate_token)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField(default=default_expiry)
    used_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"Verification for {self.user.username}"

    @property
    def is_expired(self):
        return timezone.now() >= self.expires_at

    @property
    def is_used(self):
        return self.used_at is not None

    @property
    def is_valid(self):
        return not self.is_used and not self.is_expired
