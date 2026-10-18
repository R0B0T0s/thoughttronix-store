"""Review views — thin per the architecture convention.

Every response re-renders the product's whole Reviews section partial, the
one swap target (#reviews). Products are looked up in the full product
set, not ``available()`` — unavailable products can be reviewed.
"""

from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.exceptions import PermissionDenied
from django.db import IntegrityError, transaction
from django.shortcuts import get_object_or_404, render
from django.views import View

from products.models import Product

from .forms import AuthorReviewForm
from .models import Review


def section_context(user, product, form=None):
    """Everything the Reviews section shows: the summary, the user's own
    review (pinned in "Your review"), everyone else's reviews, and — when
    the user may post one — the author form (``form`` when re-rendering an
    invalid submission)."""
    reviews = product.reviews.select_related("user")
    own_review = None
    if user.is_authenticated:
        own_review = next((r for r in reviews if r.user_id == user.pk), None)
    if form is None and Review.can_review(user, product):
        form = AuthorReviewForm()
    return {
        "product": product,
        "user": user,
        "summary": product.reviews.summary(),
        "own_review": own_review,
        "reviews": [r for r in reviews if r is not own_review],
        "form": form,
    }


def render_section(request, product, form=None):
    return render(
        request,
        "reviews/partials/_section.html",
        section_context(request.user, product, form),
    )


class ReviewSectionView(View):
    """HTMX: the Reviews section for anyone — also how Cancel restores it."""

    def get(self, request, pk):
        return render_section(request, get_object_or_404(Product, pk=pk))


class CreateReviewView(LoginRequiredMixin, View):
    """HTMX: post the signed-in user's review of a product.

    The purchase rule is enforced here on every request, whatever the page
    showed. A duplicate — a double-submit or a stale second tab — isn't an
    error: the section simply comes back showing the review already posted.
    """

    def post(self, request, pk):
        product = get_object_or_404(Product, pk=pk)
        if Review.objects.filter(user=request.user, product=product).exists():
            return render_section(request, product)
        if not Review.can_review(request.user, product):
            raise PermissionDenied
        form = AuthorReviewForm(
            request.POST, instance=Review(user=request.user, product=product)
        )
        if not form.is_valid():
            return render_section(request, product, form)
        try:
            with transaction.atomic():
                form.save()
        except IntegrityError:
            pass  # A simultaneous request posted it first; show that one.
        return render_section(request, product)
