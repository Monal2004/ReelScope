from django.contrib import admin

from .models import Movie


@admin.register(Movie)
class MovieAdmin(admin.ModelAdmin):
    list_display = ["title", "genre", "release_date", "director", "created_at"]
    list_filter = ["genre", "language"]
    search_fields = ["title", "director", "cast"]
    prepopulated_fields = {"slug": ("title",)}
