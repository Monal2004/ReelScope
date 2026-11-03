"""Tracking ID generation.

Format: RS-2026-A8K92

- "RS" identifies the platform.
- The year makes IDs easy to talk about.
- Five random characters come from a cryptographically secure source.
- The alphabet avoids letters and digits that look alike (I, O, 0, 1), so a
  visitor can retype an ID from an email without confusion.
"""

import secrets

from django.utils import timezone

ALPHABET = "ABCDEFGHJKLMNPQRSTUVWXYZ23456789"  # 32 characters
CODE_LENGTH = 5


def generate_tracking_code():
    """Return the random part of a Tracking ID, e.g. 'A8K92'."""
    return "".join(secrets.choice(ALPHABET) for _ in range(CODE_LENGTH))


def generate_tracking_id():
    """Return a new Tracking ID, e.g. 'RS-2026-A8K92'."""
    year = timezone.localdate().year
    return f"RS-{year}-{generate_tracking_code()}"


def generate_unique_tracking_id():
    """Return a Tracking ID that is not already used by an existing feedback row.

    A database unique constraint is still the final guarantee; this loop simply
    avoids the common collision case (the chance is tiny: 32^5 per year).
    """
    from .models import Feedback  # imported here to avoid a circular import

    for _ in range(10):
        tracking_id = generate_tracking_id()
        if not Feedback.objects.filter(tracking_id=tracking_id).exists():
            return tracking_id
    # Extremely unlikely: fall back to a longer random suffix.
    return f"RS-{timezone.localdate().year}-{secrets.token_hex(4).upper()}"
