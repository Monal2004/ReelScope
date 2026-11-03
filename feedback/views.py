from django.db import transaction
from django.shortcuts import get_object_or_404, redirect, render

from movies.services import movie_cards

from .forms import FeedbackForm
from .models import Feedback, SentimentAnalysis
from .tracking import generate_unique_tracking_id


def submit_feedback(request, slug):
    """Feedback form page and submission handler.

    GET: renders the feedback form for a published movie.
    POST: validates the form, saves the feedback with a unique tracking ID,
    creates a pending SentimentAnalysis row, and redirects to the success page.
    """
    movie = get_object_or_404(movie_cards().filter(is_published=True), slug=slug)

    if request.method == "POST":
        form = FeedbackForm(request.POST)
        if form.is_valid():
            # Honeypot: if the hidden website field is filled, treat as spam.
            if form.cleaned_data.get("website"):
                form.add_error(None, "Submission rejected.")
                return render(
                    request,
                    "feedback/submit.html",
                    {"movie": movie, "form": form},
                )

            with transaction.atomic():
                feedback = Feedback.objects.create(
                    movie=movie,
                    username=form.cleaned_data["username"],
                    email=form.cleaned_data["email"],
                    rating=int(form.cleaned_data["rating"]),
                    message=form.cleaned_data["message"],
                    tracking_id=generate_unique_tracking_id(),
                )
                # Create a pending analysis row so Module 3 can populate it.
                # The feedback row is committed even if analysis later fails.
                SentimentAnalysis.objects.create(
                    feedback=feedback,
                    status=SentimentAnalysis.Status.PENDING,
                )

            return redirect("feedback:success", tracking_id=feedback.tracking_id)

    else:
        form = FeedbackForm()

    return render(
        request,
        "feedback/submit.html",
        {"movie": movie, "form": form},
    )


def feedback_success(request, tracking_id):
    """Feedback submission confirmation page.

    Displays the tracking ID and submission summary. Never exposes the
    submitter's email address.
    """
    feedback = get_object_or_404(
        Feedback.objects.select_related("movie", "analysis"),
        tracking_id=tracking_id,
    )
    return render(
        request,
        "feedback/success.html",
        {"feedback": feedback},
    )


def track_feedback(request):
    """Tracking form page (GET only). Results handled in a later module."""
    return render(request, "feedback/track.html")
