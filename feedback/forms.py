from django import forms

RATING_CHOICES = [(value, f"{value} star{'s' if value != 1 else ''}") for value in range(1, 6)]


class FeedbackForm(forms.Form):
    """Visitor feedback form.

    Saved and analysed by the backend flow in a later phase; the fields and
    validation rules live here so the browser and server always agree.
    """

    username = forms.CharField(
        max_length=100,
        label="Your name",
        widget=forms.TextInput(attrs={"placeholder": "e.g. Maya Rao", "autocomplete": "name"}),
    )
    email = forms.EmailField(
        label="Email address",
        help_text="Used only to send your Tracking ID. Never shown publicly.",
        widget=forms.EmailInput(attrs={"placeholder": "you@example.com", "autocomplete": "email"}),
    )
    rating = forms.ChoiceField(
        choices=RATING_CHOICES,
        label="Your rating",
        widget=forms.RadioSelect(attrs={"class": "star-input"}),
    )
    message = forms.CharField(
        label="Your feedback",
        min_length=10,
        max_length=2000,
        widget=forms.Textarea(
            attrs={
                "rows": 6,
                "placeholder": "What worked? What didn't? Mention the story, acting, music, pacing…",
                "data-counter-target": "message-counter",
            }
        ),
    )
    # Honeypot: real visitors never see or fill this field.
    website = forms.CharField(
        required=False,
        widget=forms.HiddenInput(attrs={"tabindex": "-1", "autocomplete": "off"}),
    )

    def clean_message(self):
        message = self.cleaned_data["message"].strip()
        if len(message) < 10:
            raise forms.ValidationError("Please write at least 10 characters.")
        return message
