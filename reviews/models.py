from datetime import timedelta

from django.conf import settings
from django.db import models
from django.utils import timezone

from orders.models import OrderItem
from products.models import Product

# How long after posting a save still counts as part of posting.
EDIT_GRACE = timedelta(minutes=1)


class ReviewQuerySet(models.QuerySet):
    def summary(self):
        """The rating summary for these reviews: average stars to one
        decimal (None when there are none) and the review count."""
        totals = self.aggregate(average=models.Avg("rating"), count=models.Count("pk"))
        if totals["average"] is not None:
            totals["average"] = round(totals["average"], 1)
        return totals


class Review(models.Model):
    """One customer's rating of one product, with an optional comment.

    A customer may review a product only once they've bought it; that rule
    is checked when the review is created, never afterwards.
    """

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="reviews",
    )
    product = models.ForeignKey(
        Product, on_delete=models.CASCADE, related_name="reviews"
    )
    rating = models.PositiveSmallIntegerField()
    comment = models.TextField(max_length=2000, blank=True)
    # default (not auto_now_add) so the seed can backdate reviews.
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)
    edited_by_staff = models.BooleanField(default=False)

    objects = ReviewQuerySet.as_manager()

    class Meta:
        ordering = ["-created_at", "-pk"]
        constraints = [
            models.UniqueConstraint(
                fields=["user", "product"], name="unique_user_product_review"
            ),
            models.CheckConstraint(
                condition=models.Q(rating__gte=1, rating__lte=5),
                name="review_rating_1_to_5",
            ),
        ]

    def __str__(self):
        return f"{self.rating}★ {self.product.name} by {self.user.username}"

    @classmethod
    def can_review(cls, user, product):
        """Whether the user may post a review of the product: signed in,
        has bought it, and hasn't reviewed it yet."""
        return (
            user.is_authenticated
            and OrderItem.objects.purchased_by(user, product).exists()
            and not cls.objects.filter(user=user, product=product).exists()
        )

    @property
    def reviewer_name(self):
        """First name and last initial ("Casey M."), never the full name;
        the username when no first name is set."""
        first, last = self.user.first_name.strip(), self.user.last_name.strip()
        if not first:
            return self.user.username
        return f"{first} {last[0]}." if last else first

    @property
    def was_edited(self):
        """Whether the review was changed after it was posted — updated
        more than a minute after creation, so the creation save itself (and
        an instant double-save) never counts."""
        return self.updated_at - self.created_at > EDIT_GRACE
