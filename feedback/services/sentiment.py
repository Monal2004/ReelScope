"""Sentiment analysis service using VADER.

This module provides reusable sentiment analysis for feedback messages.
It is intentionally modular so the engine can be replaced or improved later.

Limitations:
- VADER is tuned for English text. Non-English or mixed-language feedback may
  be misclassified.
- Sarcasm, irony, and indirect opinions are not reliably detected.
- Results are best-effort estimates, not ground truth.
"""

from datetime import timedelta
from django.utils import timezone
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer

# VADER compound score thresholds. Centralized for easy adjustment.
POSITIVE_THRESHOLD = 0.05
NEGATIVE_THRESHOLD = -0.05

# Singleton analyzer instance (VADER is thread-safe for read-only scoring).
_analyzer = None


def get_analyzer():
    """Return a shared VADER SentimentIntensityAnalyzer instance."""
    global _analyzer
    if _analyzer is None:
        _analyzer = SentimentIntensityAnalyzer()
    return _analyzer


def classify_text_sentiment(text):
    """Classify a text string into Positive / Neutral / Negative.

    Returns:
        (label, score) where label is one of 'positive', 'neutral', 'negative'
        and score is the VADER compound score in [-1.0, 1.0].
    """
    analyzer = get_analyzer()
    scores = analyzer.polarity_scores(text)
    compound = scores["compound"]

    if compound >= POSITIVE_THRESHOLD:
        label = "positive"
    elif compound <= NEGATIVE_THRESHOLD:
        label = "negative"
    else:
        label = "neutral"

    return label, compound


def classify_rating_sentiment(rating):
    """Classify a star rating (1-5) into sentiment.

    Mapping:
        4-5 stars -> positive
        3 stars   -> neutral
        1-2 stars -> negative
    """
    if rating >= 4:
        return "positive"
    if rating == 3:
        return "neutral"
    return "negative"


def analyze_feedback(feedback):
    """Run sentiment analysis on a Feedback instance.

    Updates the existing SentimentAnalysis record in place. Never creates a
    duplicate record. If analysis fails, marks the record as failed with an
    error message and increments attempts. The Feedback row itself is never
    touched or rolled back.

    Returns:
        The updated SentimentAnalysis instance.
    """
    from feedback.models import SentimentAnalysis

    analysis = getattr(feedback, "analysis", None)
    if analysis is None:
        analysis = SentimentAnalysis.objects.create(
            feedback=feedback,
            status=SentimentAnalysis.Status.PENDING,
        )

    analysis.attempts = (analysis.attempts or 0) + 1
    analysis.analyzed_at = timezone.now()

    try:
        text_label, text_score = classify_text_sentiment(feedback.message)
        rating_label = classify_rating_sentiment(feedback.rating)

        analysis.text_sentiment = text_label
        analysis.text_score = text_score
        analysis.rating_sentiment = rating_label
        analysis.status = SentimentAnalysis.Status.SUCCESS
        analysis.error_message = ""

        # Mismatch: text sentiment and rating sentiment disagree.
        analysis.is_mismatch = text_label != rating_label

    except Exception as exc:  # noqa: BLE001 — capture any analysis failure
        analysis.status = SentimentAnalysis.Status.FAILED
        analysis.error_message = str(exc)
        analysis.text_sentiment = ""
        analysis.text_score = 0.0
        analysis.rating_sentiment = ""
        analysis.is_mismatch = False

    analysis.save()
    return analysis


def retry_failed_analyses(limit=None):
    """Retry sentiment analysis for all failed SentimentAnalysis records.

    Args:
        limit: Maximum number of records to retry (None = all).

    Returns:
        (processed, succeeded, failed) counts.
    """
    from feedback.models import SentimentAnalysis

    queryset = SentimentAnalysis.objects.filter(
        status=SentimentAnalysis.Status.FAILED
    ).select_related("feedback")

    if limit is not None:
        queryset = queryset[:limit]

    processed = 0
    succeeded = 0
    failed = 0

    for analysis in queryset:
        processed += 1
        try:
            analyze_feedback(analysis.feedback)
            if analysis.feedback.analysis.status == SentimentAnalysis.Status.SUCCESS:
                succeeded += 1
            else:
                failed += 1
        except Exception:  # noqa: BLE001
            failed += 1

    return processed, succeeded, failed
