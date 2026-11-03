from django import forms

from .models import Movie


class MovieForm(forms.ModelForm):
    """Form for adding and editing movies (staff only)."""

    class Meta:
        model = Movie
        fields = [
            "title",
            "description",
            "poster",
            "genre",
            "release_date",
            "director",
            "cast",
            "language",
            "is_published",
        ]
        widgets = {
            "release_date": forms.DateInput(
                attrs={"type": "date", "class": "form-control"}
            ),
            "description": forms.Textarea(
                attrs={"rows": 4, "class": "form-control"}
            ),
            "cast": forms.Textarea(
                attrs={"rows": 3, "class": "form-control"}
            ),
            "title": forms.TextInput(attrs={"class": "form-control"}),
            "director": forms.TextInput(attrs={"class": "form-control"}),
            "language": forms.TextInput(attrs={"class": "form-control"}),
            "genre": forms.Select(attrs={"class": "form-control"}),
            "is_published": forms.CheckboxInput(attrs={"class": "form-check-input"}),
            "poster": forms.ClearableFileInput(attrs={"class": "form-control"}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["is_published"].label = "Publish publicly"
        self.fields["is_published"].help_text = (
            "Unpublished movies are hidden from public visitors."
        )
