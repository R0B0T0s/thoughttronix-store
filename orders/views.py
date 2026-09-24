"""Cart and checkout views — thin per the architecture convention.

The three HTMX interactions of the core live here: add-to-cart, quantity
change, and line removal. Each renders a partial (never ``base.html``);
the responses carry the navbar badge as an out-of-band swap via the
``oob_badge`` context flag. Checkout is conventional full-page work:
validate the form, hand everything to ``place_order``.
"""

from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.views import View
from django.views.generic import DetailView, FormView, ListView, TemplateView

from accounts.mixins import StaffRequiredMixin
from accounts.models import Address
from products.models import Product

from .forms import CheckoutForm, OrderStatusForm
from .models import Cart, CartItem, Order
from .services import place_order


class CartView(LoginRequiredMixin, TemplateView):
    """The customer's cart page."""

    template_name = "orders/cart.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["cart"] = Cart.for_user(self.request.user)
        return context


class AddToCartView(LoginRequiredMixin, View):
    """HTMX: add a product; the button swaps and the badge updates OOB.

    Looks the product up through ``available()``, so adding an
    unavailable product 404s — the same not-for-sale semantics as the
    public catalog.
    """

    def post(self, request, pk):
        product = get_object_or_404(Product.objects.available(), pk=pk)
        item = Cart.for_user(request.user).add(product)
        return render(
            request,
            "orders/partials/_add_button.html",
            {"product": product, "in_cart": item.quantity, "oob_badge": True},
        )


class CartItemActionView(LoginRequiredMixin, View):
    """Base for HTMX line mutations: act, then re-render the cart contents.

    Items are always fetched through the owner's cart — never by bare pk.
    """

    def post(self, request, pk):
        item = get_object_or_404(CartItem, pk=pk, cart__user=request.user)
        self.act(item)
        return render(
            request,
            "orders/partials/_cart_contents.html",
            {"cart": item.cart, "oob_badge": True},
        )

    def act(self, item):
        raise NotImplementedError


class IncrementCartItemView(CartItemActionView):
    def act(self, item):
        item.increment()


class DecrementCartItemView(CartItemActionView):
    def act(self, item):
        item.decrement()


class RemoveCartItemView(CartItemActionView):
    def act(self, item):
        item.delete()


def _address_initial(prefix, address):
    """The ``CheckoutForm`` initial data for one address slot ("shipping"
    or "billing"), from a saved ``Address`` — shared by the checkout
    page's first render and its HTMX address-picker swap."""
    return {
        f"{prefix}_name": address.recipient_name,
        f"{prefix}_street": address.street,
        f"{prefix}_line2": address.line2,
        f"{prefix}_city": address.city,
        f"{prefix}_state": address.state,
        f"{prefix}_zip": address.zip_code,
    }


class CheckoutView(LoginRequiredMixin, FormView):
    """The single checkout page: validate the form, hand off to the service.

    A cart that can't check out (empty, or holding a product that has
    since become unavailable) is sent back to the cart page to be fixed —
    ``place_order`` enforces the same rules transactionally as the
    backstop.
    """

    template_name = "orders/checkout.html"
    form_class = CheckoutForm

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return super().dispatch(request, *args, **kwargs)
        cart = Cart.for_user(request.user)
        if not cart.items.exists():
            messages.info(request, "Your cart is empty — add something first.")
            return redirect("orders:cart")
        unavailable = [
            line.product.name for line in cart.lines() if not line.product.is_available
        ]
        if unavailable:
            messages.warning(
                request,
                f"No longer available: {', '.join(unavailable)}. "
                "Remove them from the cart to check out.",
            )
            return redirect("orders:cart")
        return super().dispatch(request, *args, **kwargs)

    def get_initial(self):
        initial = super().get_initial()
        initial["email"] = self.request.user.email
        default_shipping = Address.objects.filter(
            user=self.request.user, is_default_shipping=True
        ).first()
        if default_shipping:
            initial.update(_address_initial("shipping", default_shipping))
        default_billing = Address.objects.filter(
            user=self.request.user, is_default_billing=True
        ).first()
        if default_billing:
            initial.update(_address_initial("billing", default_billing))
        return initial

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["cart"] = Cart.for_user(self.request.user)
        addresses = Address.objects.filter(user=self.request.user)
        context["addresses"] = addresses
        default_shipping = addresses.filter(is_default_shipping=True).first()
        default_billing = addresses.filter(is_default_billing=True).first()
        context["selected_shipping_address_id"] = (
            str(default_shipping.pk) if default_shipping else ""
        )
        context["selected_billing_address_id"] = (
            str(default_billing.pk) if default_billing else ""
        )
        return context

    def form_valid(self, form):
        cart = Cart.for_user(self.request.user)
        order = place_order(cart, self.request.user, form.cleaned_data)
        self._save_addresses(form.cleaned_data)
        messages.success(self.request, f"Order {order.number} placed. Thank you!")
        return redirect(reverse("orders:confirmation", kwargs={"pk": order.pk}))

    def _save_addresses(self, data):
        """Optionally save the typed shipping/billing address to the
        customer's account, per the checkout page's "save this address"
        checkboxes. A freshly saved address becomes the default for its
        purpose only when the customer doesn't already have one.
        """
        user = self.request.user
        if data["save_shipping_address"]:
            address = Address.objects.create(
                user=user,
                label=data["shipping_address_label"] or "Shipping address",
                recipient_name=data["shipping_name"],
                street=data["shipping_street"],
                line2=data["shipping_line2"],
                city=data["shipping_city"],
                state=data["shipping_state"],
                zip_code=data["shipping_zip"],
            )
            if not Address.objects.filter(user=user, is_default_shipping=True).exists():
                address.make_default_shipping()
        if data["save_billing_address"]:
            address = Address.objects.create(
                user=user,
                label=data["billing_address_label"] or "Billing address",
                recipient_name=data["billing_name"],
                street=data["billing_street"],
                line2=data["billing_line2"],
                city=data["billing_city"],
                state=data["billing_state"],
                zip_code=data["billing_zip"],
            )
            if not Address.objects.filter(user=user, is_default_billing=True).exists():
                address.make_default_billing()


class LoadAddressFieldsView(LoginRequiredMixin, View):
    """HTMX: swap one checkout address section from a saved address.

    Renders a fresh, unbound ``CheckoutForm`` seeded only with that
    section's initial data — the rest of the page, and whatever the
    customer had already typed elsewhere, is untouched since only this
    section's ``<div>`` is swapped. An empty/missing ``address`` clears
    the section back to a blank "new address" state.
    """

    prefix = None
    partial_template = None

    def get(self, request):
        address_id = request.GET.get("address") or None
        initial = {}
        if address_id:
            address = get_object_or_404(Address, pk=address_id, user=request.user)
            initial = _address_initial(self.prefix, address)
        form = CheckoutForm(initial=initial)
        return render(
            request,
            self.partial_template,
            {
                "form": form,
                "addresses": Address.objects.filter(user=request.user),
                "selected_address_id": address_id,
            },
        )


class LoadShippingAddressView(LoadAddressFieldsView):
    prefix = "shipping"
    partial_template = "orders/partials/_shipping_fields.html"


class LoadBillingAddressView(LoadAddressFieldsView):
    prefix = "billing"
    partial_template = "orders/partials/_billing_fields.html"


class OwnOrdersMixin(LoginRequiredMixin):
    """Orders are always fetched through the owner — never by bare pk."""

    def get_queryset(self):
        return Order.objects.filter(user=self.request.user)


class OrderConfirmationView(OwnOrdersMixin, DetailView):
    template_name = "orders/confirmation.html"
    context_object_name = "order"


class OrderHistoryView(OwnOrdersMixin, ListView):
    """The customer's orders, most recent first per the model ordering."""

    template_name = "orders/order_history.html"
    context_object_name = "orders"


class OrderDetailView(OwnOrdersMixin, DetailView):
    template_name = "orders/order_detail.html"
    context_object_name = "order"

    def get_queryset(self):
        return super().get_queryset().prefetch_related("items")


# --- The back office --------------------------------------------------------
#
# Staff-only order oversight: every customer's orders, filterable by
# status, with the status dropdown on the detail page. The ``section``
# context entry drives the active tab in the staff shell.


class ManageOrderListView(StaffRequiredMixin, ListView):
    """All orders, most recent first, filterable via ``?status=``."""

    template_name = "orders/manage_orders.html"
    context_object_name = "orders"
    paginate_by = 20
    extra_context = {"section": "orders"}

    def get_queryset(self):
        orders = Order.objects.select_related("user")
        status = self.request.GET.get("status", "")
        if status in Order.Status.values:
            orders = orders.filter(status=status)
        return orders

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["statuses"] = Order.Status.choices
        context["active_status"] = self.request.GET.get("status", "")
        return context


class ManageOrderDetailView(StaffRequiredMixin, DetailView):
    """Any order's detail, with the status form alongside."""

    template_name = "orders/manage_order_detail.html"
    context_object_name = "order"
    queryset = Order.objects.select_related("user").prefetch_related("items")
    extra_context = {"section": "orders"}

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["status_form"] = OrderStatusForm(instance=self.object)
        return context


class UpdateOrderStatusView(StaffRequiredMixin, View):
    """POST-only: set an order's status from the back-office dropdown."""

    def post(self, request, pk):
        order = get_object_or_404(Order, pk=pk)
        form = OrderStatusForm(request.POST, instance=order)
        if form.is_valid():
            form.save()
            messages.success(
                request,
                f"{order.number} is now {order.get_status_display().lower()}.",
            )
        else:
            messages.error(request, "That isn't a status an order can have.")
        return redirect("orders:manage_order_detail", pk=order.pk)
