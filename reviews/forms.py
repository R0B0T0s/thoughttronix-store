"""Review forms. Each owns its validation; an invalid one re-renders the
Reviews section with its errors and the user's input."""

from django import forms

from .models import Review


class AuthorReviewForm(forms.ModelForm):
    """The author's review: 1 to 5 stars, required, and an optional comment
    (length-limited by the model field)."""

    rating = forms.TypedChoiceField(
        choices=[(stars, stars) for stars in range(1, 6)],
        coerce=int,
        widget=forms.RadioSelect,
        error_messages={"required": "Choose a star rating."},
    )

    class Meta:
        model = Review
        fields = ["rating", "comment"]


class StaffReviewForm(forms.ModelForm):
    """Staff moderating someone else's review: the comment only. There's no
    rating field, so a posted rating is never read."""

    class Meta:
        model = Review
        fields = ["comment"]
