"""All analytics queries live here.

Views stay short: they call these functions and return templates or JSON.
Every number is calculated from the database — nothing is hardcoded.
"""

from collections import Counter
from datetime import timedelta

from django.db.models import Avg, Count
from django.db.models.functions import TruncDate
from django.utils import timezone

from feedback.models import Feedback, SentimentAnalysis
from movies.models import Movie

SENTIMENTS = ("positive", "neutral", "negative")
SUCCESS = SentimentAnalysis.Status.SUCCESS


def sentiment_breakdown(feedback_queryset=None):
    """Counts, percentages and total of successful analyses."""
    queryset = SentimentAnalysis.objects.filter(status=SUCCESS)
    if feedback_queryset is not None:
        queryset = queryset.filter(feedback__in=feedback_queryset)

    counts = {key: 0 for key in SENTIMENTS}
    for row in queryset.values("text_sentiment").annotate(n=Count("id")):
        if row["text_sentiment"] in counts:
            counts[row["text_sentiment"]] = row["n"]

    total = sum(counts.values())
    percentages = {
        key: round((value / total) * 100, 1) if total else 0.0
        for key, value in counts.items()
    }
    return {
        "counts": counts,
        "percentages": percentages,
        "total": total,
    }


def aspect_leaderboard(feedback_queryset=None, limit=6):
    """Most mentioned positive aspects and negative complaints."""
    queryset = SentimentAnalysis.objects.filter(status=SUCCESS)
    if feedback_queryset is not None:
        queryset = queryset.filter(feedback__in=feedback_queryset)

    positive = Counter()
    negative = Counter()
    for positive_aspects, negative_aspects in queryset.values_list(
        "positive_aspects", "negative_aspects"
    ):
        positive.update(positive_aspects or [])
        negative.update(negative_aspects or [])

    return {
        "positive": positive.most_common(limit),
        "negative": negative.most_common(limit),
    }


def rating_breakdown(feedback_queryset):
    """How many 1–5 star ratings a movie received."""
    counts = {value: 0 for value in range(1, 6)}
    for row in feedback_queryset.values("rating").annotate(n=Count("id")):
        counts[row["rating"]] = row["n"]
    return counts


def overall_stats():
    feedback = Feedback.objects.aggregate(total=Count("id"), avg=Avg("rating"))
    return {
        "total_movies": Movie.objects.count(),
        "total_feedback": feedback["total"] or 0,
        "average_rating": round(feedback["avg"] or 0, 2),
    }


def dashboard_context():
    stats = overall_stats()
    sentiment = sentiment_breakdown()
    recent = (
        Feedback.objects.select_related("movie", "analysis")
        .order_by("-created_at")[:8]
    )
    top_movies = (
        Movie.objects.annotate(
            average_rating=Avg("feedback__rating"),
            feedback_count=Count("feedback", distinct=True),
        )
        .filter(feedback_count__gt=0)
        .order_by("-average_rating", "-feedback_count")[:5]
    )
    mismatches = SentimentAnalysis.objects.filter(
        status=SUCCESS, is_mismatch=True
    ).count()

    return {
        **stats,
        "sentiment": sentiment,
        "recent_feedback": recent,
        "top_movies": top_movies,
        "mismatch_count": mismatches,
        "today": timezone.localdate(),
    }


def movie_ratings_chart():
    rows = (
        Movie.objects.annotate(
            average_rating=Avg("feedback__rating"),
            feedback_count=Count("feedback", distinct=True),
        )
        .filter(feedback_count__gt=0)
        .order_by("-average_rating")[:10]
    )
    return {
        "labels": [row.title for row in rows],
        "ratings": [round(float(row.average_rating), 2) for row in rows],
        "counts": [row.feedback_count for row in rows],
    }


def sentiment_by_movie_chart():
    rows = (
        Feedback.objects.values("movie__title", "analysis__text_sentiment")
        .filter(analysis__status=SUCCESS)
        .annotate(n=Count("id"))
        .order_by("movie__title")
    )

    movies = []
    series = {key: [] for key in SENTIMENTS}
    for row in rows:
        title = row["movie__title"]
        if title not in movies:
            movies.append(title)
            for key in SENTIMENTS:
                series[key].append(0)
        index = movies.index(title)
        label = row["analysis__text_sentiment"]
        if label in series:
            series[label][index] = row["n"]

    return {"labels": movies, **series}


def feedback_trend_chart(days=30):
    """Daily feedback volume with positive and negative lines."""
    end = timezone.localdate()
    start = end - timedelta(days=days - 1)

    rows = (
        Feedback.objects.filter(created_at__date__gte=start)
        .values("created_at__date", "analysis__text_sentiment")
        .annotate(n=Count("id"))
    )

    by_day = {}
    for row in rows:
        day = row["created_at__date"].isoformat()
        entry = by_day.setdefault(day, {"total": 0, "positive": 0, "negative": 0})
        entry["total"] += row["n"]
        sentiment = row["analysis__text_sentiment"]
        if sentiment in ("positive", "negative"):
            entry[sentiment] += row["n"]

    labels = []
    totals = []
    positive = []
    negative = []
    for offset in range(days):
        day = (start + timedelta(days=offset)).isoformat()
        entry = by_day.get(day, {"total": 0, "positive": 0, "negative": 0})
        labels.append(day)
        totals.append(entry["total"])
        positive.append(entry["positive"])
        negative.append(entry["negative"])

    return {
        "labels": labels,
        "total": totals,
        "positive": positive,
        "negative": negative,
    }
