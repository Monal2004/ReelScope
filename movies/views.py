from django.contrib.admin.views.decorators import staff_member_required
from django.core.paginator import Paginator
from django.db.models import Avg, Count, Q
from django.shortcuts import get_object_or_404, redirect, render

from analytics.services import (
    aspect_leaderboard,
    rating_breakdown,
    sentiment_breakdown,
)
from analytics.services.ranking import get_movie_ranking
from feedback.models import Feedback

from .forms import MovieForm
from .models import Movie
from .services import movie_cards


def home(request):
    """Landing page: featured movie, newest releases and top-rated titles."""
    movies = movie_cards().filter(is_published=True)
    featured = (
        movies.filter(feedback_count__gt=0)
        .order_by("-average_rating", "-feedback_count")
        .first()
        or movies.order_by("-created_at").first()
    )

    feedback = Feedback.objects.aggregate(total=Count("id"), avg=Avg("rating"))

    return render(
        request,
        "home.html",
        {
            "featured": featured,
            "latest_movies": movies.order_by("-created_at")[:6],
            "top_movies": movies.filter(feedback_count__gt=0).order_by(
                "-average_rating", "-feedback_count"
            )[:3],
            "genres": Movie.Genre.choices,
            "stats": {
                "movies": Movie.objects.count(),
                "feedback": feedback["total"] or 0,
                "average": round(feedback["avg"] or 0, 1),
            },
        },
    )


def movie_list(request):
    """Browse published movies with search, genre filter and pagination."""
    queryset = movie_cards().filter(is_published=True).order_by("-created_at")

    query = (request.GET.get("q") or "").strip()
    genre = (request.GET.get("genre") or "").strip().lower()

    if query:
        queryset = queryset.filter(
            Q(title__icontains=query)
            | Q(director__icontains=query)
            | Q(cast__icontains=query)
            | Q(description__icontains=query)
        )
    if genre in Movie.Genre.values:
        queryset = queryset.filter(genre=genre)
    else:
        genre = ""

    paginator = Paginator(queryset, 9)
    page_obj = paginator.get_page(request.GET.get("page"))

    params = request.GET.copy()
    params.pop("page", None)

    return render(
        request,
        "movies/list.html",
        {
            "page_obj": page_obj,
            "movies": page_obj.object_list,
            "genres": Movie.Genre.choices,
            "active_genre": genre,
            "query": query,
            "query_suffix": params.urlencode(),
        },
    )


def movie_detail(request, slug):
    """Public movie page with rating summary and recent audience feedback."""
    movie = get_object_or_404(movie_cards().filter(is_published=True), slug=slug)
    feedback_queryset = movie.feedback.select_related("analysis").order_by(
        "-created_at"
    )

    return render(
        request,
        "movies/detail.html",
        {
            "movie": movie,
            "recent_feedback": feedback_queryset[:6],
            "feedback_total": feedback_queryset.count(),
            "rating_counts": rating_breakdown(feedback_queryset),
            "sentiment": sentiment_breakdown(feedback_queryset),
            "aspects": aspect_leaderboard(feedback_queryset),
            "movie_ranking": get_movie_ranking(movie),
        },
    )


@staff_member_required
def movie_list_staff(request):
    """Staff view: list all movies with publish status."""
    movies = Movie.objects.all().order_by("-created_at")
    return render(
        request,
        "staff/movie_list.html",
        {"movies": movies},
    )


@staff_member_required
def movie_add(request):
    """Staff view: add a new movie."""
    if request.method == "POST":
        form = MovieForm(request.POST, request.FILES)
        if form.is_valid():
            movie = form.save()
            return redirect("movies_staff:movie_list_staff")
    else:
        form = MovieForm()
    return render(
        request,
        "staff/movie_form.html",
        {"form": form, "action": "Add"},
    )


@staff_member_required
def movie_edit(request, pk):
    """Staff view: edit an existing movie."""
    movie = get_object_or_404(Movie, pk=pk)
    if request.method == "POST":
        form = MovieForm(request.POST, request.FILES, instance=movie)
        if form.is_valid():
            form.save()
            return redirect("movies_staff:movie_list_staff")
    else:
        form = MovieForm(instance=movie)
    return render(
        request,
        "staff/movie_form.html",
        {"form": form, "movie": movie, "action": "Edit"},
    )


@staff_member_required
def movie_delete(request, pk):
    """Staff view: delete a movie with confirmation."""
    movie = get_object_or_404(Movie, pk=pk)
    feedback_count = movie.feedback.count()
    if request.method == "POST":
        movie.delete()
        return redirect("movies_staff:movie_list_staff")
    return render(
        request,
        "staff/movie_confirm_delete.html",
        {"movie": movie, "feedback_count": feedback_count},
    )


@staff_member_required
def movie_toggle_publish(request, pk):
    """Staff view: toggle a movie's published status."""
    movie = get_object_or_404(Movie, pk=pk)
    movie.is_published = not movie.is_published
    movie.save()
    return redirect("movies_staff:movie_list_staff")
