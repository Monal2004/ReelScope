"""Read-only queries for movie pages."""

from django.db.models import Avg, Count

from .models import Movie


def movie_cards():
    """Movies annotated with rating information for cards and detail pages."""
    return Movie.objects.annotate(
        average_rating=Avg("feedback__rating"),
        feedback_count=Count("feedback", distinct=True),
    )
