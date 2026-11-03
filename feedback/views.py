from django.shortcuts import get_object_or_404, render
from django.views.decorators.http import require_GET

from movies.services import movie_cards

from .forms import FeedbackForm


@require_GET
def submit_feedback(request, slug):
    """Feedback form page.

    The submission, tracking-ID and analysis flow is added in the backend
    phase; this phase delivers the complete, validated UI.
    """
    movie = get_object_or_404(movie_cards(), slug=slug)
    return render(
        request,
        "feedback/submit.html",
        {"movie": movie, "form": FeedbackForm()},
    )


@require_GET
def track_feedback(request):
    """Tracking form page; results are rendered once the backend exists."""
    return render(request, "feedback/track.html")
