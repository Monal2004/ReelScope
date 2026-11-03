from django.contrib.admin.views.decorators import staff_member_required
from django.http import JsonResponse
from django.shortcuts import render

from . import services
from .services import ranking


@staff_member_required
def dashboard(request):
    """Staff overview: real totals, sentiment split, charts, and movie ranking."""
    context = services.dashboard_context()
    context["ranked_movies"] = ranking.get_ranked_movies(limit=10)
    context["insufficient_movies"] = ranking.get_insufficient_data_movies(limit=10)
    return render(request, "staff/dashboard.html", context)


@staff_member_required
def chart_summary(request):
    stats = services.overall_stats()
    sentiment = services.sentiment_breakdown()
    return JsonResponse({**stats, **sentiment})


@staff_member_required
def chart_ratings(request):
    return JsonResponse(services.movie_ratings_chart())


@staff_member_required
def chart_sentiment_by_movie(request):
    return JsonResponse(services.sentiment_by_movie_chart())


@staff_member_required
def chart_trends(request):
    try:
        days = int(request.GET.get("days", 30))
    except (TypeError, ValueError):
        days = 30
    days = max(7, min(days, 90))
    return JsonResponse(services.feedback_trend_chart(days))
