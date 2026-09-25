"""Coupon model tests: redemption rules and discount calculation.

``check_redeemable`` never raises — every rejection is a plain message —
and ``discount_for`` never returns more than what it's discounting.
"""

from datetime import timedelta
from decimal import Decimal

import pytest
from django.utils import timezone

from orders.models import Order

from .models import Coupon

pytestmark = pytest.mark.django_db


def make_coupon(**overrides):
    now = timezone.now()
    data = {
        "code": "TESTCODE",
        "discount_type": Coupon.DiscountType.PERCENT,
        "discount_value": Decimal("10"),
        "valid_from": now - timedelta(days=1),
        "valid_until": now + timedelta(days=1),
    }
    data.update(overrides)
    return Coupon.objects.create(**data)


# --- check_redeemable ------------------------------------------------------


def test_a_fresh_active_coupon_is_redeemable(customer, cart, cart_item):
    coupon = make_coupon()

    assert coupon.check_redeemable(customer, cart) is None


def test_a_retired_coupon_is_rejected(customer, cart, cart_item):
    coupon = make_coupon(is_active=False)

    assert coupon.check_redeemable(customer, cart) == "This code is no longer active."


def test_a_not_yet_started_coupon_is_rejected(customer, cart, cart_item):
    now = timezone.now()
    coupon = make_coupon(
        valid_from=now + timedelta(days=1), valid_until=now + timedelta(days=10)
    )

    assert coupon.check_redeemable(customer, cart) == "This code isn't active yet."


def test_an_expired_coupon_is_rejected(customer, cart, cart_item):
    now = timezone.now()
    coupon = make_coupon(
        valid_from=now - timedelta(days=10), valid_until=now - timedelta(days=1)
    )

    assert coupon.check_redeemable(customer, cart) == "This code has expired."


def test_a_product_scoped_coupon_needs_that_product_in_the_cart(
    customer, cart, cart_item, unavailable_product
):
    coupon = make_coupon()
    coupon.products.add(unavailable_product)

    error = coupon.check_redeemable(customer, cart)

    assert error == "This code applies to EchoPatch, which isn't in your cart."


def test_a_product_scoped_coupon_is_redeemable_when_the_product_is_in_the_cart(
    customer, cart, cart_item
):
    coupon = make_coupon()
    coupon.products.add(cart_item.product)

    assert coupon.check_redeemable(customer, cart) is None


def test_a_customer_cannot_reuse_a_code_theyve_already_used(customer, cart, cart_item):
    coupon = make_coupon()
    Order.objects.create(
        user=customer,
        total=Decimal("9.00"),
        coupon_code=coupon.code,
        email="casey@example.com",
        shipping_name="Casey Monroe",
        shipping_street="9 Synapse Court",
        shipping_city="Canyon",
        shipping_state="TX",
        shipping_zip="79015",
        billing_name="Casey Monroe",
        billing_street="9 Synapse Court",
        billing_city="Canyon",
        billing_state="TX",
        billing_zip="79015",
        card_last4="4242",
    )

    assert coupon.check_redeemable(customer, cart) == "You've already used this code."


# --- discount_for ------------------------------------------------------------


def test_percent_discount_on_an_order_wide_coupon(cart, cart_item):
    coupon = make_coupon(
        discount_type=Coupon.DiscountType.PERCENT, discount_value=Decimal("10")
    )

    assert coupon.discount_for(cart) == Decimal("70.00")  # 10% of 699.98


def test_fixed_discount_on_a_product_scoped_coupon_ignores_quantity(cart, cart_item):
    coupon = make_coupon(
        discount_type=Coupon.DiscountType.FIXED, discount_value=Decimal("10.00")
    )
    coupon.products.add(cart_item.product)  # 2 units in the cart

    assert coupon.discount_for(cart) == Decimal("10.00")


def test_discount_never_exceeds_what_it_discounts(cart, cart_item):
    coupon = make_coupon(
        discount_type=Coupon.DiscountType.FIXED, discount_value=Decimal("1000.00")
    )

    assert coupon.discount_for(cart) == cart.total()


# --- Display helpers -----------------------------------------------------


def test_is_order_wide_reflects_whether_products_are_set(cart_item):
    coupon = make_coupon()
    assert coupon.is_order_wide

    coupon.products.add(cart_item.product)
    assert not coupon.is_order_wide


def test_status_label_reflects_active_window_and_flag():
    now = timezone.now()

    assert make_coupon(code="A").status_label == "Active"
    assert (
        make_coupon(code="B", valid_from=now + timedelta(days=1)).status_label
        == "Scheduled"
    )
    assert (
        make_coupon(code="C", valid_until=now - timedelta(hours=1)).status_label
        == "Expired"
    )
    assert make_coupon(code="D", is_active=False).status_label == "Retired"
