"""CheckoutForm tests — coverage priority 2 in the PRD.

Each declarative rule rejects bad input with a field-specific error;
a fully valid form passes. Most of this needs no database — the coupon
tests at the bottom are the exception, since redemption depends on a
real cart and coupon.
"""

from datetime import timedelta

import pytest
from django.utils import timezone

from .forms import CheckoutForm

VALID_DATA = {
    "email": "casey@example.com",
    "shipping_name": "Casey Monroe",
    "shipping_street": "12 Cortex Lane",
    "shipping_line2": "Unit 7",
    "shipping_city": "Canyon",
    "shipping_state": "TX",
    "shipping_zip": "79015",
    "billing_name": "Casey Monroe",
    "billing_street": "12 Cortex Lane",
    "billing_line2": "",
    "billing_city": "Canyon",
    "billing_state": "TX",
    "billing_zip": "79015-1234",
    "card_number": "4242 4242 4242 4242",
    "card_expiry": "12/39",
    "card_cvv": "123",
}


def form_with(**overrides):
    return CheckoutForm(data={**VALID_DATA, **overrides})


def test_a_fully_valid_form_passes():
    assert form_with().is_valid()


def test_line2_is_optional_but_everything_else_is_required():
    required = [name for name in VALID_DATA if not name.endswith("_line2")]
    for name in required:
        form = form_with(**{name: ""})
        assert not form.is_valid()
        assert form.errors[name] == ["This field is required."]


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("email", "not-an-email"),
        ("shipping_state", "XX"),  # not one of the 50 states + DC
        ("billing_state", "Texas"),
        ("shipping_zip", "790"),
        ("billing_zip", "79015-12"),
        ("card_number", "4242 4242 4242 4241"),  # fails Luhn
        ("card_expiry", "01/20"),  # long expired
        ("card_expiry", "13/30"),  # no thirteenth month
        ("card_cvv", "12"),
        ("card_cvv", "abcd"),
    ],
)
def test_each_rule_rejects_bad_input_on_its_own_field(field, value):
    form = form_with(**{field: value})

    assert not form.is_valid()
    assert field in form.errors
    assert len(form.errors) == 1  # the error lands beside its field, alone


def test_the_form_declares_only_one_imperative_rule():
    """The showcase contract: declarative rules only, with one deliberate
    exception — coupon redemption depends on the cart and user, not just
    the field's own value, so it's the form's only ``clean_*`` method."""
    assert "clean" not in CheckoutForm.__dict__
    imperative = [name for name in CheckoutForm.__dict__ if name.startswith("clean_")]
    assert imperative == ["clean_coupon_code"]


# --- Coupon redemption ---------------------------------------------------


def test_coupon_code_is_optional():
    assert form_with().is_valid()


def test_a_valid_coupon_is_accepted(cart, cart_item, coupon):
    form = CheckoutForm(
        data={**VALID_DATA, "coupon_code": coupon.code}, cart=cart, user=cart.user
    )

    assert form.is_valid(), form.errors
    assert form.cleaned_data["coupon_code"] == coupon


def test_an_unknown_code_is_rejected(cart, cart_item):
    form = CheckoutForm(
        data={**VALID_DATA, "coupon_code": "NOPE"}, cart=cart, user=cart.user
    )

    assert not form.is_valid()
    assert form.errors["coupon_code"] == ["That code isn't valid."]


def test_an_expired_code_is_rejected(cart, cart_item, coupon):
    coupon.valid_until = timezone.now() - timedelta(days=1)
    coupon.save()

    form = CheckoutForm(
        data={**VALID_DATA, "coupon_code": coupon.code}, cart=cart, user=cart.user
    )

    assert not form.is_valid()
    assert form.errors["coupon_code"] == ["This code has expired."]
