"""The address book: the Address model, its form, and its owner-scoped
CRUD and default-toggle views.
"""

from http import HTTPStatus

import pytest
from django.contrib.auth import get_user_model
from django.urls import reverse

from .forms import AddressForm
from .models import Address

# --- The Address model --------------------------------------------------------


def test_str_includes_label_and_user(address):
    assert str(address) == f"Home ({address.user})"


def test_make_default_shipping_unsets_the_previous_default(customer, address):
    other = Address.objects.create(
        user=customer,
        label="Office",
        recipient_name="Casey Monroe",
        street="1 Synapse Ave",
        city="Canyon",
        state="TX",
        zip_code="79015",
    )
    address.make_default_shipping()

    other.make_default_shipping()

    address.refresh_from_db()
    assert not address.is_default_shipping
    assert other.is_default_shipping


def test_shipping_and_billing_defaults_are_independent(customer, address):
    other = Address.objects.create(
        user=customer,
        label="Office",
        recipient_name="Casey Monroe",
        street="1 Synapse Ave",
        city="Canyon",
        state="TX",
        zip_code="79015",
    )
    address.make_default_shipping()

    other.make_default_billing()

    address.refresh_from_db()
    assert address.is_default_shipping
    assert not address.is_default_billing
    assert other.is_default_billing
    assert not other.is_default_shipping


def test_defaults_do_not_leak_across_customers(customer, address):
    other_customer = get_user_model().objects.create_user(
        username="other", password="x"
    )
    others_address = Address.objects.create(
        user=other_customer,
        label="Home",
        recipient_name="Alex Rivera",
        street="9 Neural Way",
        city="Amarillo",
        state="TX",
        zip_code="79101",
    )

    address.make_default_shipping()
    others_address.make_default_shipping()

    address.refresh_from_db()
    assert address.is_default_shipping  # untouched by another user's default


# --- AddressForm --------------------------------------------------------------

VALID_ADDRESS_DATA = {
    "label": "Home",
    "recipient_name": "Casey Monroe",
    "street": "12 Cortex Lane",
    "line2": "",
    "city": "Canyon",
    "state": "TX",
    "zip_code": "79015",
}


def test_a_fully_valid_address_form_passes():
    assert AddressForm(data=VALID_ADDRESS_DATA).is_valid()


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("state", "XX"),
        ("zip_code", "790"),
        ("label", ""),
        ("recipient_name", ""),
    ],
)
def test_each_rule_rejects_bad_input(field, value):
    form = AddressForm(data={**VALID_ADDRESS_DATA, field: value})

    assert not form.is_valid()
    assert field in form.errors


def test_line2_is_optional():
    form = AddressForm(data={**VALID_ADDRESS_DATA, "line2": "Unit 7"})

    assert form.is_valid()


# --- The address book pages ---------------------------------------------------


def test_address_list_requires_login(client, db):
    response = client.get(reverse("accounts:address_list"))

    assert response.status_code == HTTPStatus.FOUND
    assert reverse("accounts:login") in response.url


def test_address_list_has_a_designed_empty_state(client, customer):
    client.force_login(customer)

    response = client.get(reverse("accounts:address_list"))

    assert "No saved addresses yet" in response.content.decode()


def test_address_list_shows_the_customers_addresses(client, customer, address):
    client.force_login(customer)

    response = client.get(reverse("accounts:address_list"))

    assert address.label in response.content.decode()


def test_create_address_assigns_the_current_user(client, customer):
    client.force_login(customer)

    client.post(reverse("accounts:address_create"), VALID_ADDRESS_DATA)

    address = Address.objects.get()
    assert address.user == customer


def test_update_address_is_scoped_to_the_owner(client, customer, address):
    other_customer = get_user_model().objects.create_user(
        username="other", password="x"
    )
    client.force_login(other_customer)

    response = client.get(reverse("accounts:address_update", kwargs={"pk": address.pk}))

    assert response.status_code == HTTPStatus.NOT_FOUND


def test_delete_address_is_scoped_to_the_owner(client, customer, address):
    other_customer = get_user_model().objects.create_user(
        username="other", password="x"
    )
    client.force_login(other_customer)

    response = client.post(
        reverse("accounts:address_delete", kwargs={"pk": address.pk})
    )

    assert response.status_code == HTTPStatus.NOT_FOUND
    assert Address.objects.filter(pk=address.pk).exists()


def test_deleting_the_default_address_just_clears_the_default(
    client, customer, address
):
    address.make_default_shipping()
    client.force_login(customer)

    client.post(reverse("accounts:address_delete", kwargs={"pk": address.pk}))

    assert not Address.objects.exists()  # nothing auto-promoted, nothing left


def test_set_default_shipping_toggle(client, customer, address):
    client.force_login(customer)

    response = client.post(
        reverse("accounts:address_default_shipping", kwargs={"pk": address.pk})
    )

    assert response.status_code == HTTPStatus.OK
    address.refresh_from_db()
    assert address.is_default_shipping


def test_set_default_billing_toggle(client, customer, address):
    client.force_login(customer)

    response = client.post(
        reverse("accounts:address_default_billing", kwargs={"pk": address.pk})
    )

    assert response.status_code == HTTPStatus.OK
    address.refresh_from_db()
    assert address.is_default_billing


def test_toggling_defaults_is_scoped_to_the_owner(client, customer, address):
    other_customer = get_user_model().objects.create_user(
        username="other", password="x"
    )
    client.force_login(other_customer)

    response = client.post(
        reverse("accounts:address_default_shipping", kwargs={"pk": address.pk})
    )

    assert response.status_code == HTTPStatus.NOT_FOUND
    address.refresh_from_db()
    assert not address.is_default_shipping
