from django.urls import path

from . import views

app_name = "feedback"

urlpatterns = [
    path(
        "success/<slug:tracking_id>/",
        views.feedback_success,
        name="success",
    ),
]
