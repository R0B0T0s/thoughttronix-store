from django.conf import settings
from django.db import models

from products.models import Product


class Wishlist(models.Model):
    """A customer's wishlist — one per user, created lazily on first touch.

    It has no name and no sharing fields: it is simply "my wishlist."

    Deliberately NOT registered in the Django admin, and there is no
    back-office tab. Unlike the cart and the address book, a wishlist is
    reachable only by its owner, so customers' private interests stay
    private. Do not "fix" the missing admin registration.
    """

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="wishlist",
    )

    def __str__(self):
        return f"Wishlist for {self.user.username}"

    @classmethod
    def for_user(cls, user):
        """Return the user's wishlist, creating it on first touch."""
        wishlist, _ = cls.objects.get_or_create(user=user)
        return wishlist

    def add(self, product):
        """Save a product; a repeat add is a no-op."""
        item, _ = self.items.get_or_create(product=product)
        return item

    def remove(self, product):
        """Remove a product; removing an unsaved product is a no-op."""
        self.items.filter(product=product).delete()

    def contains(self, product):
        """Whether the product is currently saved."""
        return self.items.filter(product=product).exists()


class WishlistItem(models.Model):
    """One saved product; the wishlist–product pair is unique."""

    wishlist = models.ForeignKey(
        Wishlist, on_delete=models.CASCADE, related_name="items"
    )
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    added_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-added_at"]
        constraints = [
            models.UniqueConstraint(
                fields=["wishlist", "product"], name="unique_wishlist_product"
            )
        ]

    def __str__(self):
        return self.product.name
