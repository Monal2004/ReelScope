from django.urls import path

from feedback.views import submit_feedback

from . import views

app_name = "movies"

urlpatterns = [
    path("", views.movie_list, name="list"),
    path("<slug:slug>/", views.movie_detail, name="detail"),
    path("<slug:slug>/feedback/", submit_feedback, name="feedback"),
]
