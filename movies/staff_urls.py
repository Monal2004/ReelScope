from django.urls import path

from . import views

app_name = "movies_staff"

urlpatterns = [
    path("", views.movie_list_staff, name="movie_list_staff"),
    path("add/", views.movie_add, name="movie_add"),
    path("<int:pk>/edit/", views.movie_edit, name="movie_edit"),
    path("<int:pk>/delete/", views.movie_delete, name="movie_delete"),
    path("<int:pk>/toggle-publish/", views.movie_toggle_publish, name="movie_toggle_publish"),
]
