from django.urls import path

from . import views

app_name = "analytics"

urlpatterns = [
    path("", views.dashboard, name="dashboard"),
    path("data/summary/", views.chart_summary, name="chart_summary"),
    path("data/ratings/", views.chart_ratings, name="chart_ratings"),
    path("data/sentiment/", views.chart_sentiment_by_movie, name="chart_sentiment"),
    path("data/trends/", views.chart_trends, name="chart_trends"),
]
