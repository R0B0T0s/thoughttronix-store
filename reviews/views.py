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

from .forms import AuthorReviewForm, StaffReviewForm
from .models import Review


def section_context(user, product, form=None, editing=None):
    """Everything the Reviews section shows: the summary, the user's own
    review (pinned in "Your review"), everyone else's reviews, and — when
    the user may post one — the author form (``form`` when re-rendering an
    invalid submission). With ``editing``, ``form`` is instead the edit
    form shown in place of that review — the author's pinned box or, for
    staff, its card in the list."""
    reviews = product.reviews.select_related("user")
    own_review = None
    if user.is_authenticated:
        own_review = next((r for r in reviews if r.user_id == user.pk), None)
    edit_form = form if editing else None
    create_form = None if editing else form
    if create_form is None and Review.can_review(user, product):
        create_form = AuthorReviewForm()
    return {
        "product": product,
        "user": user,
        "summary": product.reviews.summary(),
        "own_review": own_review,
        "reviews": [r for r in reviews if r is not own_review],
        "form": create_form,
        "editing": editing,
        "edit_form": edit_form,
    }


def render_section(request, product, form=None, editing=None):
    return render(
        request,
        "reviews/partials/_section.html",
        section_context(request.user, product, form, editing),
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


class EditReviewView(LoginRequiredMixin, View):
    """HTMX: GET swaps the review to a pre-filled form in place; POST saves
    the edit. Either way the section comes back.

    The author (staff included, for their own review) gets the full author
    form. Staff editing someone else's review get the comment-only staff
    form, and the save marks it "Edited by staff".
    """

    def get_review(self, request, pk):
        review = get_object_or_404(Review, pk=pk)
        if not review.can_change(request.user):
            raise PermissionDenied
        return review

    def get_form_class(self, request, review):
        if review.user_id == request.user.pk:
            return AuthorReviewForm
        return StaffReviewForm

    def get(self, request, pk):
        review = self.get_review(request, pk)
        form = self.get_form_class(request, review)(instance=review)
        return render_section(request, review.product, form, editing=review)

    def post(self, request, pk):
        review = self.get_review(request, pk)
        form = self.get_form_class(request, review)(request.POST, instance=review)
        if not form.is_valid():
            # The section re-reads reviews from the database, so the saved
            # version shows everywhere but the form, which keeps the input.
            return render_section(request, review.product, form, editing=review)
        if isinstance(form, StaffReviewForm):
            review.staff_edit(form.cleaned_data["comment"])
        else:
            review.author_edit(
                form.cleaned_data["rating"], form.cleaned_data["comment"]
            )
        return render_section(request, review.product)


class DeleteReviewView(LoginRequiredMixin, View):
    """HTMX: delete a review — its author or any staff member — and return
    the section. For the author, the empty form comes back."""

    def post(self, request, pk):
        review = get_object_or_404(Review, pk=pk)
        if not review.can_change(request.user):
            raise PermissionDenied
        review.delete()
        return render_section(request, review.product)
