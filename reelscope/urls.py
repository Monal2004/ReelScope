"""Root URL configuration for ReelScope.

App URL modules are added as their pages are built in later phases.
"""

from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import path

urlpatterns = [
    path("django-admin/", admin.site.urls),
]

if settings.DEBUG:
    # Serve uploaded posters during development only.
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
