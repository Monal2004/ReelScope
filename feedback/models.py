from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models

from movies.models import Movie

from .tracking import generate_unique_tracking_id


class Feedback(models.Model):
    """One movie feedback submission from any visitor (login not required)."""

    movie = models.ForeignKey(
        Movie, on_delete=models.CASCADE, related_name="feedback"
    )
    username = models.CharField(max_length=100)
    email = models.EmailField()
    rating = models.PositiveSmallIntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)]
    )
    message = models.TextField()
    tracking_id = models.CharField(
        max_length=16,
        unique=True,
        editable=False,
        db_index=True,
        default=generate_unique_tracking_id,
    )
    email_sent_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["movie", "created_at"]),
        ]

    def __str__(self):
        return f"{self.tracking_id} — {self.movie.title} ({self.rating}★)"


class SentimentAnalysis(models.Model):
    """The stored result of analysing a feedback message.

    A separate table keeps the visitor's feedback safe: if analysis fails, only
    this row records the failure and the feedback itself is never lost.
    """

    class Sentiment(models.TextChoices):
        POSITIVE = "positive", "Positive"
        NEUTRAL = "neutral", "Neutral"
        NEGATIVE = "negative", "Negative"

    class Status(models.TextChoices):
        PENDING = "pending", "Pending"
        SUCCESS = "success", "Success"
        FAILED = "failed", "Failed"

    feedback = models.OneToOneField(
        Feedback, on_delete=models.CASCADE, related_name="analysis"
    )
    text_sentiment = models.CharField(
        max_length=10, choices=Sentiment.choices, blank=True
    )
    text_score = models.FloatField(default=0.0)
    rating_sentiment = models.CharField(
        max_length=10, choices=Sentiment.choices, blank=True
    )
    is_mismatch = models.BooleanField(default=False)
    positive_aspects = models.JSONField(default=list, blank=True)
    negative_aspects = models.JSONField(default=list, blank=True)
    status = models.CharField(
        max_length=10, choices=Status.choices, default=Status.PENDING, db_index=True
    )
    error_message = models.TextField(blank=True)
    attempts = models.PositiveSmallIntegerField(default=0)
    analyzed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        verbose_name_plural = "sentiment analyses"
        ordering = ["-feedback__created_at"]

    def __str__(self):
        return f"Analysis for {self.feedback.tracking_id} ({self.status})"
