from django.core.validators import FileExtensionValidator
from django.db import models
from django.urls import reverse
from django.utils.text import slugify

from .validators import validate_not_future, validate_poster_size


class Movie(models.Model):
    """A movie that visitors can browse and leave feedback for."""

    class Genre(models.TextChoices):
        ACTION = "action", "Action"
        COMEDY = "comedy", "Comedy"
        DRAMA = "drama", "Drama"
        SCI_FI = "sci-fi", "Sci-Fi"
        THRILLER = "thriller", "Thriller"
        HORROR = "horror", "Horror"
        ROMANCE = "romance", "Romance"
        ANIMATION = "animation", "Animation"
        DOCUMENTARY = "documentary", "Documentary"

    title = models.CharField(max_length=200)
    slug = models.SlugField(max_length=220, unique=True, blank=True)
    description = models.TextField()
    poster = models.ImageField(
        upload_to="posters/",
        validators=[
            FileExtensionValidator(["jpg", "jpeg", "png", "webp"]),
            validate_poster_size,
        ],
    )
    genre = models.CharField(max_length=20, choices=Genre.choices)
    release_date = models.DateField(validators=[validate_not_future])
    director = models.CharField(max_length=150)
    cast = models.TextField(help_text="Comma-separated list of main actors.")
    language = models.CharField(max_length=50)
    is_published = models.BooleanField(
        default=False,
        help_text="Only published movies are visible to public visitors.",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return self.title

    def save(self, *args, **kwargs):
        """Create a unique slug from the title when one is not supplied."""
        if not self.slug:
            base = slugify(self.title)[:200] or "movie"
            slug = base
            counter = 2
            while Movie.objects.filter(slug=slug).exclude(pk=self.pk).exists():
                slug = f"{base}-{counter}"
                counter += 1
            self.slug = slug
        super().save(*args, **kwargs)

    def get_absolute_url(self):
        return reverse("movies:detail", kwargs={"slug": self.slug})
