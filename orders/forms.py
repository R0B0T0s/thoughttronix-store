"""The checkout form — the codebase's showcase of declarative validation.

Every rule is visible at its field declaration, in the style of data
annotations: field types validate (``EmailField``), field arguments
validate (``required``, ``max_length``, ``ChoiceField``), and the
``validators=[...]`` list carries the rest. The one exception is
``coupon_code``: whether a code is redeemable depends on the cart and
the user, not on the field's own value in isolation, so it gets the
form's only ``clean_*`` method.
"""

from django import forms
from django.core.validators import RegexValidator

from accounts.validators import US_STATES, zip_validator
from coupons.models import Coupon

from .models import Order
from .validators import validate_card_number, validate_expiry

cvv_validator = RegexValidator(r"^\d{3,4}$", "Enter the 3- or 4-digit CVV.")


SHIPPING_ADDRESS_FIELDS = [
    "shipping_name",
    "shipping_street",
    "shipping_line2",
    "shipping_city",
    "shipping_state",
    "shipping_zip",
]
BILLING_ADDRESS_FIELDS = [
    "billing_name",
    "billing_street",
    "billing_line2",
    "billing_city",
    "billing_state",
    "billing_zip",
]


class CheckoutForm(forms.Form):
    """One page, one POST: contact, shipping, billing, payment.

    ``save_shipping_address``/``save_billing_address`` and their label
    fields are checkout-only extras, not part of ``ADDRESS_FIELDS`` in
    ``orders/services.py`` — ``place_order`` never sees them. They're
    read directly by ``CheckoutView`` to optionally save an ``Address``
    once the order itself has been placed.
    """

    email = forms.EmailField(label="Email")

    shipping_name = forms.CharField(label="Full name", max_length=100)
    shipping_street = forms.CharField(label="Street address", max_length=200)
    shipping_line2 = forms.CharField(
        label="Apt, suite, etc. (optional)", max_length=200, required=False
    )
    shipping_city = forms.CharField(label="City", max_length=100)
    shipping_state = forms.ChoiceField(label="State", choices=US_STATES)
    shipping_zip = forms.CharField(
        label="ZIP code", max_length=10, validators=[zip_validator]
    )
    save_shipping_address = forms.BooleanField(
        label="Save this address to my account", required=False
    )
    shipping_address_label = forms.CharField(
        label="Label (e.g. Home, Work)", max_length=50, required=False
    )

    billing_name = forms.CharField(label="Full name", max_length=100)
    billing_street = forms.CharField(label="Street address", max_length=200)
    billing_line2 = forms.CharField(
        label="Apt, suite, etc. (optional)", max_length=200, required=False
    )
    billing_city = forms.CharField(label="City", max_length=100)
    billing_state = forms.ChoiceField(label="State", choices=US_STATES)
    billing_zip = forms.CharField(
        label="ZIP code", max_length=10, validators=[zip_validator]
    )
    save_billing_address = forms.BooleanField(
        label="Save this address to my account", required=False
    )
    billing_address_label = forms.CharField(
        label="Label (e.g. Home, Work)", max_length=50, required=False
    )

    card_number = forms.CharField(
        label="Card number", max_length=23, validators=[validate_card_number]
    )
    card_expiry = forms.CharField(
        label="Expiry (MM/YY)", max_length=5, validators=[validate_expiry]
    )
    card_cvv = forms.CharField(label="CVV", max_length=4, validators=[cvv_validator])

    coupon_code = forms.CharField(label="Coupon code", max_length=32, required=False)

    def __init__(self, *args, cart=None, user=None, **kwargs):
        self.cart = cart
        self.user = user
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            widget = field.widget
            if isinstance(widget, forms.CheckboxInput):
                widget.attrs["class"] = "checkbox"
            elif isinstance(widget, forms.Select):
                widget.attrs["class"] = "select w-full"
            else:
                widget.attrs["class"] = "input w-full"

    # Field groups for the template — the form owns its own structure.

    def shipping_fields(self):
        return [self[name] for name in SHIPPING_ADDRESS_FIELDS]

    def billing_fields(self):
        return [self[name] for name in BILLING_ADDRESS_FIELDS]

    def card_fields(self):
        return [self[name] for name in self.fields if name.startswith("card_")]

    def clean_coupon_code(self):
        code = self.cleaned_data["coupon_code"]
        if not code:
            return None
        try:
            coupon = Coupon.objects.get(code=code)
        except Coupon.DoesNotExist:
            raise forms.ValidationError("That code isn't valid.") from None
        error = coupon.check_redeemable(self.user, self.cart)
        if error:
            raise forms.ValidationError(error)
        return coupon


class OrderStatusForm(forms.ModelForm):
    """The back-office status dropdown — any of the four states, anytime.

    Guarding the workflow (no un-cancelling, no re-shipping a delivered
    order) is deliberately left as a student exercise.
    """

    class Meta:
        model = Order
        fields = ["status"]
        widgets = {"status": forms.Select(attrs={"class": "select"})}
