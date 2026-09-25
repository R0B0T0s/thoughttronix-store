"""The back-office coupon form.

Widgets get DaisyUI classes in the same shared ``__init__`` loop used by
``products.forms.StyledModelForm``. Two rules need imperative validation
since they span more than one field: a percent discount cannot exceed
100, and the active window has to end after it starts.
"""

from decimal import Decimal

from django import forms

from .models import Coupon


class StyledModelForm(forms.ModelForm):
    """Base form that dresses every widget in DaisyUI classes."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            widget = field.widget
            if isinstance(widget, forms.CheckboxInput):
                widget.attrs["class"] = "toggle toggle-primary"
            elif isinstance(widget, forms.SelectMultiple):
                widget.attrs["class"] = "select h-auto w-full"
                widget.attrs.setdefault("size", 8)
            elif isinstance(widget, forms.Select):
                widget.attrs["class"] = "select w-full"
            else:
                widget.attrs["class"] = "input w-full"


class CouponForm(StyledModelForm):
    valid_from = forms.DateTimeField(
        widget=forms.DateTimeInput(
            attrs={"type": "datetime-local"}, format="%Y-%m-%dT%H:%M"
        ),
        input_formats=["%Y-%m-%dT%H:%M"],
    )
    valid_until = forms.DateTimeField(
        widget=forms.DateTimeInput(
            attrs={"type": "datetime-local"}, format="%Y-%m-%dT%H:%M"
        ),
        input_formats=["%Y-%m-%dT%H:%M"],
    )

    class Meta:
        model = Coupon
        fields = [
            "code",
            "discount_type",
            "discount_value",
            "products",
            "valid_from",
            "valid_until",
            "is_active",
        ]

    def clean(self):
        cleaned_data = super().clean()
        discount_type = cleaned_data.get("discount_type")
        discount_value = cleaned_data.get("discount_value")
        if (
            discount_type == Coupon.DiscountType.PERCENT
            and discount_value is not None
            and discount_value > Decimal("100")
        ):
            self.add_error("discount_value", "A percentage discount cannot exceed 100.")

        valid_from = cleaned_data.get("valid_from")
        valid_until = cleaned_data.get("valid_until")
        if valid_from and valid_until and valid_until <= valid_from:
            self.add_error("valid_until", "The end must be after the start.")
        return cleaned_data
