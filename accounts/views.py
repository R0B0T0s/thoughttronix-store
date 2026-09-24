from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.views import LoginView, LogoutView
from django.contrib.messages.views import SuccessMessageMixin
from django.shortcuts import get_object_or_404, render
from django.urls import reverse_lazy
from django.views import View
from django.views.generic import CreateView, DeleteView, ListView, UpdateView

from .forms import AddressForm, SignInForm, SignupForm
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


class SignOutView(LogoutView):
    def post(self, request, *args, **kwargs):
        # Flash after super() has flushed the session, or the message
        # would be wiped along with it.
        response = super().post(request, *args, **kwargs)
        messages.info(request, "You have signed out.")
        return response


# --- The address book --------------------------------------------------------
#
# A customer's saved addresses, reusable at checkout. Addresses are
# always fetched through the owner — never by bare pk, matching the
# convention orders already uses for carts and orders.


class OwnAddressesMixin(LoginRequiredMixin):
    def get_queryset(self):
        return Address.objects.filter(user=self.request.user)


class AddressListView(OwnAddressesMixin, ListView):
    template_name = "accounts/address_list.html"
    context_object_name = "addresses"


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
