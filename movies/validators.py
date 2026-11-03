"""Validation helpers for uploaded movie posters."""

from django.core.exceptions import ValidationError
from django.utils import timezone

MAX_POSTER_SIZE = 5 * 1024 * 1024  # 5 MB


def validate_poster_size(image):
    """Reject poster files larger than 5 MB."""
    if image.size > MAX_POSTER_SIZE:
        raise ValidationError("Poster must be 5 MB or smaller.")


def validate_not_future(date):
    """Release dates cannot be in the future."""
    if date and date > timezone.localdate():
        raise ValidationError("Release date cannot be in the future.")
