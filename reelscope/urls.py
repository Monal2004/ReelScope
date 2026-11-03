"""Root URL configuration for ReelScope."""

from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path

from feedback.views import track_feedback
from movies.views import home

urlpatterns = [
    path("", home, name="home"),
    path("movies/", include("movies.urls")),
    path("staff/movies/", include("movies.staff_urls")),
    path("feedback/", include("feedback.urls")),
    path("track/", track_feedback, name="track"),
    path("accounts/", include("accounts.urls")),
    path("staff/", include("analytics.urls")),
    path("django-admin/", admin.site.urls),
]

if settings.DEBUG:
    # Serve uploaded posters during development only.
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
