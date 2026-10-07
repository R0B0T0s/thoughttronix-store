from http import HTTPStatus

from django.conf import settings
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.views import (
    LoginView,
    LogoutView,
    PasswordChangeView,
    PasswordResetCompleteView,
    PasswordResetConfirmView,
    PasswordResetDoneView,
    PasswordResetView,
)
from django.contrib.messages.views import SuccessMessageMixin
from django.shortcuts import get_object_or_404, render
from django.urls import reverse_lazy
from django.views import View
from django.views.generic import (
    CreateView,
    DeleteView,
    FormView,
    ListView,
    TemplateView,
    UpdateView,
)

from . import services
from .forms import (
    AddressForm,
    EmailChangeForm,
    SignInForm,
    SignupForm,
    StyledPasswordChangeForm,
    StyledPasswordResetForm,
    StyledSetPasswordForm,
)
from .models import Address


class SignupView(SuccessMessageMixin, CreateView):
    """Create a customer account, then hand off to the login page.

    New users sign in themselves — auto-login after signup is left as a
    student exercise.
    """

    form_class = SignupForm
    template_name = "accounts/signup.html"
    success_url = reverse_lazy("accounts:login")
    success_message = "Account created — you can now sign in."


class SignInView(LoginView):
    template_name = "accounts/login.html"
    authentication_form = SignInForm


def locked_out(request, original_response=None, credentials=None):
    """django-axes' lockout response: the styled page, not a bare message."""
    minutes = int(settings.AXES_COOLOFF_TIME.total_seconds() // 60)
    return render(
        request,
        "accounts/locked_out.html",
        {"cooloff_minutes": minutes},
        status=HTTPStatus.TOO_MANY_REQUESTS,
    )


class SignOutView(LogoutView):
    def post(self, request, *args, **kwargs):
        # Flash after super() has flushed the session, or the message
        # would be wiped along with it.
        response = super().post(request, *args, **kwargs)
        messages.info(request, "You have signed out.")
        return response


# --- The Account page ----------------------------------------------------------


class AccountView(LoginRequiredMixin, TemplateView):
    template_name = "accounts/account.html"


class EmailChangeView(LoginRequiredMixin, FormView):
    form_class = EmailChangeForm
    template_name = "accounts/email_change.html"
    success_url = reverse_lazy("accounts:account")

    def get_form_kwargs(self):
        return {**super().get_form_kwargs(), "user": self.request.user}

    def form_valid(self, form):
        old_email = self.request.user.email
        user = form.save()
        services.notify_email_changed(user, old_email)
        messages.success(self.request, f"Your email is now {user.email}.")
        return super().form_valid(form)


class AccountPasswordChangeView(PasswordChangeView):
    """Django's password change view, styled and namespaced.

    The stock view is already login-required, and it keeps this session
    signed in while the new password hash signs out every other session.
    """

    form_class = StyledPasswordChangeForm
    template_name = "accounts/password_change.html"
    success_url = reverse_lazy("accounts:account")

    def form_valid(self, form):
        response = super().form_valid(form)
        services.notify_password_changed(form.user)
        messages.success(
            self.request,
            "Your password was changed. Other devices have been signed out.",
        )
        return response


# --- Password reset ------------------------------------------------------------
#
# Django's four built-in reset views, styled and mounted under the
# ``accounts`` namespace. The stock views redirect to un-namespaced URL
# names, so each success_url is pointed at ours.


class AccountPasswordResetView(PasswordResetView):
    """Email a one-hour, single-use reset link.

    Registered and unknown addresses get the identical "check your inbox"
    redirect, so the form can't be used to discover who has an account.
    """

    form_class = StyledPasswordResetForm
    template_name = "accounts/password_reset.html"
    subject_template_name = "accounts/emails/password_reset_subject.txt"
    email_template_name = "accounts/emails/password_reset.txt"
    success_url = reverse_lazy("accounts:password_reset_done")


class AccountPasswordResetDoneView(PasswordResetDoneView):
    template_name = "accounts/password_reset_done.html"


class AccountPasswordResetConfirmView(PasswordResetConfirmView):
    """Set a new password from a reset link — or, for an expired or
    already-used link, explain and point back to the request form.
    """

    form_class = StyledSetPasswordForm
    template_name = "accounts/password_reset_confirm.html"
    success_url = reverse_lazy("accounts:password_reset_complete")


class AccountPasswordResetCompleteView(PasswordResetCompleteView):
    template_name = "accounts/password_reset_complete.html"


# --- The address book --------------------------------------------------------
#
# A customer's saved addresses, reusable at checkout. Addresses are
# always fetched through the owner — never by bare pk, matching the
# convention orders already uses for carts and orders.


class OwnAddressesMixin(LoginRequiredMixin):
    def get_queryset(self):
        return Address.objects.filter(user=self.request.user)


class AddressListView(OwnAddressesMixin, ListView):
    template_name = "accounts/addresses.html"
    context_object_name = "addresses"

    def get_queryset(self):
        return super().get_queryset().order_by("label")


class AddressCreateView(OwnAddressesMixin, SuccessMessageMixin, CreateView):
    form_class = AddressForm
    template_name = "accounts/address_form.html"
    success_url = reverse_lazy("accounts:address_list")
    success_message = "“%(label)s” saved."

    def form_valid(self, form):
        form.instance.user = self.request.user
        return super().form_valid(form)


class AddressUpdateView(OwnAddressesMixin, SuccessMessageMixin, UpdateView):
    form_class = AddressForm
    template_name = "accounts/address_form.html"
    success_url = reverse_lazy("accounts:address_list")
    success_message = "“%(label)s” saved."


class AddressDeleteView(OwnAddressesMixin, SuccessMessageMixin, DeleteView):
    context_object_name = "address"
    template_name = "accounts/address_confirm_delete.html"
    success_url = reverse_lazy("accounts:address_list")
    success_message = "Address deleted."


class AddressActionView(LoginRequiredMixin, View):
    """Base for HTMX default-toggle mutations: act, then re-render the list.

    Addresses are always fetched through the owner — never by bare pk.
    """

    def post(self, request, pk):
        address = get_object_or_404(Address, pk=pk, user=request.user)
        self.act(address)
        return render(
            request,
            "accounts/partials/_address_list.html",
            {"addresses": Address.objects.filter(user=request.user)},
        )

    def act(self, address):
        raise NotImplementedError


class SetDefaultShippingView(AddressActionView):
    def act(self, address):
        address.make_default_shipping()


class SetDefaultBillingView(AddressActionView):
    def act(self, address):
        address.make_default_billing()
