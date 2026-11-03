from django.contrib import admin

from .models import Feedback, SentimentAnalysis


class SentimentAnalysisInline(admin.StackedInline):
    model = SentimentAnalysis
    extra = 0


@admin.register(Feedback)
class FeedbackAdmin(admin.ModelAdmin):
    list_display = ["tracking_id", "movie", "username", "rating", "created_at"]
    list_filter = ["rating", "created_at", "movie"]
    search_fields = ["tracking_id", "username", "message"]
    readonly_fields = ["tracking_id", "created_at"]
    inlines = [SentimentAnalysisInline]


@admin.register(SentimentAnalysis)
class SentimentAnalysisAdmin(admin.ModelAdmin):
    list_display = ["feedback", "text_sentiment", "text_score", "status", "analyzed_at"]
    list_filter = ["status", "text_sentiment"]
    search_fields = ["feedback__tracking_id"]
    readonly_fields = ["analyzed_at"]
