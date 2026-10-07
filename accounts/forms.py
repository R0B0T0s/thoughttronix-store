from django import forms
from django.contrib.auth.forms import (
    AuthenticationForm,
    PasswordChangeForm,
    PasswordResetForm,
    SetPasswordForm,
    UserCreationForm,
)

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
    """The stock authentication form, dressed in DaisyUI.

    The username field also takes an email (see ``UsernameOrEmailBackend``),
    so its label and length limit allow for one.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        username = self.fields["username"]
        username.label = "Username or email"
        username.max_length = User._meta.get_field("email").max_length
        username.widget.attrs["maxlength"] = username.max_length
        for field in self.fields.values():
            field.widget.attrs["class"] = "input w-full"


class EmailChangeForm(forms.Form):
    """Change (or add) the signed-in user's email.

    The current password is required so someone at an unattended session
    can't redirect the account. The new email is checked for uniqueness
    the same way signup checks it.
    """

    email = forms.EmailField(
        label="New email", max_length=User._meta.get_field("email").max_length
    )
    current_password = forms.CharField(
        label="Current password",
        strip=False,
        widget=forms.PasswordInput(attrs={"autocomplete": "current-password"}),
    )

    def __init__(self, user, *args, **kwargs):
        self.user = user
        super().__init__(*args, **kwargs)
        self.fields["email"].widget.attrs["autocomplete"] = "email"
        for field in self.fields.values():
            field.widget.attrs["class"] = "input w-full"

    def clean_email(self):
        email = User.objects.normalize_email(self.cleaned_data["email"])
        if email.lower() == self.user.email.lower():
            raise forms.ValidationError("That's already your email.")
        if User.objects.email_in_use(email, exclude=self.user):
            raise forms.ValidationError("An account with that email already exists.")
        return email

    def clean_current_password(self):
        password = self.cleaned_data["current_password"]
        if not self.user.check_password(password):
            raise forms.ValidationError(
                "Your current password was entered incorrectly."
            )
        return password

    def save(self):
        self.user.email = self.cleaned_data["email"]
        self.user.save(update_fields=["email"])
        return self.user


class StyledPasswordChangeForm(PasswordChangeForm):
    """Django's password change form — current password plus the new one
    twice, run through the password validators — dressed in DaisyUI.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["old_password"].label = "Current password"
        for field in self.fields.values():
            field.widget.attrs["class"] = "input w-full"


class StyledPasswordResetForm(PasswordResetForm):
    """Django's reset request form, dressed in DaisyUI.

    The stock form already matches the email case-insensitively, skips
    inactive users, and sends nothing — silently — for an unknown address.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["email"].widget.attrs["class"] = "input w-full"


class StyledSetPasswordForm(SetPasswordForm):
    """Django's set-new-password form (used by a reset link), dressed in
    DaisyUI. The new password runs through the password validators.
    """

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
