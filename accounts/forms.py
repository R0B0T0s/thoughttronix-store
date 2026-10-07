from django import forms
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm

from .models import Address, User
from .validators import US_STATES, zip_validator


class SignupForm(UserCreationForm):
    """Django's stock signup fields plus a required, unique email.

    The email is how the store reaches a customer who loses access, so
    each address belongs to exactly one account, whatever its
    capitalization. The widgets carry DaisyUI classes because plain
    Django forms own their own styling here.
    """

    class Meta(UserCreationForm.Meta):
        model = User
        fields = ("username", "email")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["email"].required = True
        for field in self.fields.values():
            field.widget.attrs["class"] = "input w-full"

    def clean_email(self):
        email = User.objects.normalize_email(self.cleaned_data["email"])
        if User.objects.email_in_use(email):
            raise forms.ValidationError("An account with that email already exists.")
        return email


class SignInForm(AuthenticationForm):
    """The stock authentication form, dressed in DaisyUI."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs["class"] = "input w-full"


class AddressForm(forms.ModelForm):
    """The address-book add/edit form — the same fields and rules as
    ``CheckoutForm``'s address sections, minus the "save" checkbox,
    which only makes sense at checkout.
    """

    state = forms.ChoiceField(label="State", choices=US_STATES)
    zip_code = forms.CharField(
        label="ZIP code", max_length=10, validators=[zip_validator]
    )

    class Meta:
        model = Address
        fields = [
            "label",
            "recipient_name",
            "street",
            "line2",
            "city",
            "state",
            "zip_code",
        ]
        labels = {
            "label": "Label (e.g. Home, Work)",
            "recipient_name": "Full name",
            "street": "Street address",
            "line2": "Apt, suite, etc. (optional)",
            "city": "City",
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            widget = field.widget
            if isinstance(widget, forms.Select):
                widget.attrs["class"] = "select w-full"
            else:
                widget.attrs["class"] = "input w-full"
