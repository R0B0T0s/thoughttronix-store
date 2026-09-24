"""Checkout's saved-address integration: prefill from defaults, the HTMX
address picker, and the "save this address" checkboxes.
"""

from http import HTTPStatus

from django.contrib.auth import get_user_model
from django.urls import reverse

from accounts.models import Address

from .models import Order
from .test_checkout_form import VALID_DATA

# --- Prefill from defaults ----------------------------------------------------


def test_checkout_prefills_from_default_addresses(client, customer, cart_item, address):
    address.make_default_shipping()
    client.force_login(customer)

    response = client.get(reverse("orders:checkout"))

    form = response.context["form"]
    assert form.initial["shipping_name"] == "Casey Monroe"
    assert form.initial["shipping_street"] == "12 Cortex Lane"


def test_checkout_has_no_prefill_without_a_default(
    client, customer, cart_item, address
):
    client.force_login(customer)  # address exists but isn't a default

    response = client.get(reverse("orders:checkout"))

    assert "shipping_name" not in response.context["form"].initial


def test_checkout_hides_the_picker_with_no_saved_addresses(client, customer, cart_item):
    client.force_login(customer)

    response = client.get(reverse("orders:checkout"))

    assert "Use a saved address" not in response.content.decode()


def test_checkout_offers_the_picker_with_saved_addresses(
    client, customer, cart_item, address
):
    client.force_login(customer)

    response = client.get(reverse("orders:checkout"))

    page = response.content.decode()
    assert "Use a saved address" in page
    assert address.label in page


# --- The HTMX address-loading endpoints ---------------------------------------


def test_loading_a_saved_shipping_address_fills_the_fields(
    client, customer, cart_item, address
):
    client.force_login(customer)

    response = client.get(
        reverse("orders:load_shipping_address"), {"address": address.pk}
    )

    assert response.status_code == HTTPStatus.OK
    page = response.content.decode()
    assert "12 Cortex Lane" in page


def test_loading_with_no_address_clears_the_fields(
    client, customer, cart_item, address
):
    client.force_login(customer)

    response = client.get(reverse("orders:load_shipping_address"))

    assert "shipping_name" not in response.context["form"].initial


def test_loading_anothers_address_404s(client, customer, cart_item, address):
    other_customer = get_user_model().objects.create_user(
        username="other", password="x"
    )
    client.force_login(other_customer)

    response = client.get(
        reverse("orders:load_billing_address"), {"address": address.pk}
    )

    assert response.status_code == HTTPStatus.NOT_FOUND


# --- Saving an address from checkout -------------------------------------------


def test_checking_save_shipping_address_creates_one(client, customer, cart_item):
    client.force_login(customer)

    client.post(
        reverse("orders:checkout"), {**VALID_DATA, "save_shipping_address": "on"}
    )

    saved = Address.objects.get()
    assert saved.label == "Shipping address"
    assert saved.street == "12 Cortex Lane"
    assert saved.is_default_shipping  # first save becomes the default
    assert not saved.is_default_billing


def test_a_custom_label_is_used_when_given(client, customer, cart_item):
    client.force_login(customer)

    client.post(
        reverse("orders:checkout"),
        {
            **VALID_DATA,
            "save_shipping_address": "on",
            "shipping_address_label": "Home",
        },
    )

    assert Address.objects.get().label == "Home"


def test_leaving_the_checkbox_unchecked_saves_nothing(client, customer, cart_item):
    client.force_login(customer)

    client.post(reverse("orders:checkout"), VALID_DATA)

    assert not Address.objects.exists()


def test_saving_does_not_override_an_existing_default(
    client, customer, cart_item, address
):
    address.make_default_shipping()
    client.force_login(customer)

    client.post(
        reverse("orders:checkout"), {**VALID_DATA, "save_shipping_address": "on"}
    )

    new_address = Address.objects.exclude(pk=address.pk).get()
    assert not new_address.is_default_shipping
    address.refresh_from_db()
    assert address.is_default_shipping  # untouched


def test_both_sections_can_be_saved_independently(client, customer, cart_item):
    client.force_login(customer)

    client.post(
        reverse("orders:checkout"),
        {
            **VALID_DATA,
            "save_shipping_address": "on",
            "save_billing_address": "on",
        },
    )

    assert Address.objects.count() == 2


def test_a_failed_checkout_saves_no_address(client, customer, cart_item):
    bad = {
        **VALID_DATA,
        "card_number": "4242 4242 4242 4241",
        "save_shipping_address": "on",
    }
    client.force_login(customer)

    client.post(reverse("orders:checkout"), bad)

    assert not Order.objects.exists()
    assert not Address.objects.exists()
