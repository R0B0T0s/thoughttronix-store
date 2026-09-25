from decimal import Decimal

from django.core.validators import MinValueValidator
from django.db import models
from django.utils import timezone

from products.models import Product


class Coupon(models.Model):
    """A staff-issued discount code, redeemable at checkout.

    Order-wide or product-scoped by the same field: an empty ``products``
    means "the whole order," one or more products means "only these
    lines." ``is_active`` is a deliberate kill switch, independent of
    ``valid_from``/``valid_until`` — retiring a code early doesn't require
    guessing at or backdating its scheduled end.
    """

    class DiscountType(models.TextChoices):
        PERCENT = "PERCENT", "Percent off"
        FIXED = "FIXED", "Fixed amount off"

    code = models.CharField(max_length=32, unique=True)
    discount_type = models.CharField(max_length=10, choices=DiscountType.choices)
    discount_value = models.DecimalField(
        max_digits=10, decimal_places=2, validators=[MinValueValidator(Decimal("0.01"))]
    )
    products = models.ManyToManyField(
        Product,
        blank=True,
        related_name="coupons",
        help_text="Leave empty for an order-wide discount, or pick one or "
        "more products to limit the discount to just those lines.",
    )
    valid_from = models.DateTimeField()
    valid_until = models.DateTimeField()
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ["-valid_from"]

    def __str__(self):
        return self.code

    @property
    def discount_display(self):
        if self.discount_type == self.DiscountType.PERCENT:
            return f"{self.discount_value}% off"
        return f"${self.discount_value} off"

    @property
    def is_order_wide(self):
        return not self.products.exists()

    @property
    def status_label(self):
        """A back-office-friendly summary of where this coupon stands."""
        if not self.is_active:
            return "Retired"
        now = timezone.now()
        if now < self.valid_from:
            return "Scheduled"
        if now > self.valid_until:
            return "Expired"
        return "Active"

    def check_redeemable(self, user, cart):
        """Validate this coupon against a customer and their cart.

        Returns ``None`` if redeemable, otherwise a customer-facing
        message explaining why not. Never raises — every rejection is a
        plain message, never an exception, so a bad code can't produce
        anything worse than a form error.
        """
        if not self.is_active:
            return "This code is no longer active."
        now = timezone.now()
        if now < self.valid_from:
            return "This code isn't active yet."
        if now > self.valid_until:
            return "This code has expired."
        if not self.is_order_wide:
            cart_product_ids = {line.product_id for line in cart.lines()}
            coupon_products = self.products.all()
            matching = cart_product_ids & {product.id for product in coupon_products}
            if not matching:
                names = ", ".join(product.name for product in coupon_products)
                return f"This code applies to {names}, which isn't in your cart."
        from orders.models import Order

        if Order.objects.filter(user=user, coupon_code=self.code).exists():
            return "You've already used this code."
        return None

    def discount_for(self, cart):
        """The dollar amount this coupon takes off the given cart.

        Order-wide coupons discount the cart total; product-scoped
        coupons discount only the matching lines' combined total. Either
        way the discount is capped so it can never exceed what it's
        discounting — a coupon can zero out a line or an order, never go
        negative.
        """
        if self.is_order_wide:
            base = cart.total()
        else:
            product_ids = set(self.products.values_list("id", flat=True))
            base = sum(
                (
                    line.line_total
                    for line in cart.lines()
                    if line.product_id in product_ids
                ),
                Decimal("0.00"),
            )
        if self.discount_type == self.DiscountType.PERCENT:
            discount = (base * self.discount_value / Decimal("100")).quantize(
                Decimal("0.01")
            )
        else:
            discount = self.discount_value
        return min(discount, base)
