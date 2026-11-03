"""Movie ranking service.

Implements a transparent weighted scoring system for movies based on actual
feedback and sentiment analysis records stored in SQLite.

Formula:
    Final Score = (Rating Score × 0.50)
                + (Positive Sentiment Percentage × 0.30)
                + (Feedback Confidence × 0.20)

Components:
    Rating Score        = (Average Rating / 5) × 100          (0–100)
    Positive Sentiment % = (Positive / Analyzed) × 100        (0–100)
    Feedback Confidence = min(Feedback Count / MIN_FEEDBACK, 1) × 100   (0–100)

Minimum feedback threshold (centralized):
    MIN_FEEDBACK_FOR_RANKING = 5  (movies below this are excluded from ranking)
    CONFIDENCE_DENOMINATOR   = 20 (confidence caps at 100% at 20 submissions)

All values are computed from live database records. Nothing is hardcoded or
stored as a stale score on the Movie model.
"""

from django.db.models import Avg, Count, Q
from django.db.models.functions import Coalesce

from feedback.models import SentimentAnalysis
from movies.models import Movie

# Centralized thresholds — easy to adjust in one place.
MIN_FEEDBACK_FOR_RANKING = 5
CONFIDENCE_DENOMINATOR = 20

# Weighted formula constants (must sum to 1.0).
WEIGHT_RATING = 0.50
WEIGHT_SENTIMENT = 0.30
WEIGHT_CONFIDENCE = 0.20


def _movie_feedback_stats():
    """Return a queryset of movies annotated with feedback statistics.

    Each movie is annotated with:
        total_feedback          — count of all Feedback rows
        analyzed_feedback       — count of successfully analyzed feedback
        positive_feedback       — count of positive text sentiment
        negative_feedback       — count of negative text sentiment
        neutral_feedback        — count of neutral text sentiment
        average_rating          — average star rating (may be None)
    """
    return (
        Movie.objects.filter(is_published=True)
        .annotate(
            total_feedback=Count("feedback", distinct=True),
            average_rating=Avg("feedback__rating"),
            analyzed_feedback=Count(
                "feedback__analysis",
                filter=Q(feedback__analysis__status=SentimentAnalysis.Status.SUCCESS),
                distinct=True,
            ),
            positive_feedback=Count(
                "feedback__analysis",
                filter=Q(
                    feedback__analysis__status=SentimentAnalysis.Status.SUCCESS,
                    feedback__analysis__text_sentiment="positive",
                ),
                distinct=True,
            ),
            negative_feedback=Count(
                "feedback__analysis",
                filter=Q(
                    feedback__analysis__status=SentimentAnalysis.Status.SUCCESS,
                    feedback__analysis__text_sentiment="negative",
                ),
                distinct=True,
            ),
            neutral_feedback=Count(
                "feedback__analysis",
                filter=Q(
                    feedback__analysis__status=SentimentAnalysis.Status.SUCCESS,
                    feedback__analysis__text_sentiment="neutral",
                ),
                distinct=True,
            ),
        )
        .order_by("-total_feedback")
    )


def calculate_movie_scores():
    """Calculate ranking scores for all published movies.

    Returns:
        A list of dicts, one per published movie, ordered by final score
        (highest first). Each dict contains:

            movie               — Movie instance
            rank                — int or None (None if excluded)
            total_feedback      — int
            average_rating      — float or None
            rating_score        — float (0–100) or None
            analyzed_feedback   — int
            positive_feedback   — int
            negative_feedback   — int
            neutral_feedback    — int
            positive_pct        — float (0–100) or None
            confidence          — float (0–100)
            final_score         — float (0–100) or None
            ranking_available   — bool (True if >= min feedback AND has analyzed sentiment)
            insufficient_reason — str or None
    """
    movies = _movie_feedback_stats()
    results = []

    for movie in movies:
        total = movie.total_feedback or 0
        avg_rating = movie.average_rating
        analyzed = movie.analyzed_feedback or 0
        positive = movie.positive_feedback or 0
        negative = movie.negative_feedback or 0
        neutral = movie.neutral_feedback or 0

        # Determine if ranking is available.
        # Need at least MIN_FEEDBACK_FOR_RANKING submissions AND at least one
        # successfully analyzed feedback record for sentiment data.
        has_min_feedback = total >= MIN_FEEDBACK_FOR_RANKING
        has_sentiment = analyzed > 0
        ranking_available = has_min_feedback and has_sentiment

        # Component calculations.
        if avg_rating is not None:
            rating_score = (avg_rating / 5.0) * 100.0
        else:
            rating_score = None

        if analyzed > 0:
            positive_pct = (positive / analyzed) * 100.0
        else:
            positive_pct = None

        confidence = (min(total, CONFIDENCE_DENOMINATOR) / CONFIDENCE_DENOMINATOR) * 100.0

        # Final weighted score (only when ranking is available).
        if ranking_available:
            final_score = (
                (rating_score * WEIGHT_RATING)
                + (positive_pct * WEIGHT_SENTIMENT)
                + (confidence * WEIGHT_CONFIDENCE)
            )
        else:
            final_score = None

        # Determine insufficient-data reason.
        if total < MIN_FEEDBACK_FOR_RANKING:
            insufficient_reason = (
                f"Needs {MIN_FEEDBACK_FOR_RANKING - total} more "
                f"submission{'s' if MIN_FEEDBACK_FOR_RANKING - total != 1 else ''} "
                f"for reliable ranking."
            )
        elif not has_sentiment:
            insufficient_reason = (
                "No successfully analyzed sentiment data yet. "
                "Run sentiment analysis to enable ranking."
            )
        else:
            insufficient_reason = None

        results.append(
            {
                "movie": movie,
                "total_feedback": total,
                "average_rating": round(avg_rating, 2) if avg_rating is not None else None,
                "rating_score": round(rating_score, 2) if rating_score is not None else None,
                "analyzed_feedback": analyzed,
                "positive_feedback": positive,
                "negative_feedback": negative,
                "neutral_feedback": neutral,
                "positive_pct": round(positive_pct, 1) if positive_pct is not None else None,
                "confidence": round(confidence, 1),
                "final_score": round(final_score, 2) if final_score is not None else None,
                "ranking_available": ranking_available,
                "insufficient_reason": insufficient_reason,
            }
        )

    # Sort: movies with available ranking first (by final score desc),
    # then movies with insufficient data (by total feedback desc).
    # Tie-break: higher average rating, then higher feedback count.
    available = [r for r in results if r["ranking_available"]]
    unavailable = [r for r in results if not r["ranking_available"]]

    available.sort(
        key=lambda r: (
            r["final_score"] if r["final_score"] is not None else -1,
            r["average_rating"] if r["average_rating"] is not None else -1,
            r["total_feedback"],
        ),
        reverse=True,
    )

    unavailable.sort(
        key=lambda r: (
            r["total_feedback"],
            r["average_rating"] if r["average_rating"] is not None else -1,
        ),
        reverse=True,
    )

    sorted_results = available + unavailable

    # Assign ranks only to movies with available ranking.
    for rank, result in enumerate(sorted_results, start=1):
        if result["ranking_available"]:
            result["rank"] = rank
        else:
            result["rank"] = None

    return sorted_results


def get_ranked_movies(limit=None):
    """Return movies eligible for reliable ranking, ordered by final score.

    Args:
        limit: Maximum number of movies to return (None = all).

    Returns:
        List of result dicts (see calculate_movie_scores) for movies where
        ranking_available is True.
    """
    results = calculate_movie_scores()
    ranked = [r for r in results if r["ranking_available"]]
    if limit is not None:
        ranked = ranked[:limit]
    return ranked


def get_insufficient_data_movies(limit=None):
    """Return movies that do not qualify for reliable ranking.

    Args:
        limit: Maximum number of movies to return (None = all).

    Returns:
        List of result dicts for movies where ranking_available is False.
    """
    results = calculate_movie_scores()
    insufficient = [r for r in results if not r["ranking_available"]]
    if limit is not None:
        insufficient = insufficient[:limit]
    return insufficient


def get_movie_ranking(movie):
    """Return ranking info for a single movie.

    Args:
        movie: A Movie instance.

    Returns:
        A result dict (see calculate_movie_scores) for the given movie,
        or None if the movie is not published.
    """
    results = calculate_movie_scores()
    for result in results:
        if result["movie"].pk == movie.pk:
            return result
    return None
