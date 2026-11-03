from django.contrib.admin.views.decorators import staff_member_required
from django.http import JsonResponse
from django.shortcuts import render

from . import services


@staff_member_required
def dashboard(request):
    """Staff overview: real totals, sentiment split, charts and recent feedback."""
    return render(request, "staff/dashboard.html", services.dashboard_context())


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
