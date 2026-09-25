"""Back-office coupon management: access control, CRUD, retire/reactivate."""

from datetime import timedelta
from http import HTTPStatus

import pytest
from django.urls import reverse
from django.utils import timezone

from orders.models import Order

from .models import Coupon

pytestmark = pytest.mark.django_db


def coupon_data(**overrides):
    now = timezone.now()
    data = {
        "code": "SPRINGSALE",
        "discount_type": "PERCENT",
        "discount_value": "15.00",
        "valid_from": (now - timedelta(days=1)).strftime("%Y-%m-%dT%H:%M"),
        "valid_until": (now + timedelta(days=30)).strftime("%Y-%m-%dT%H:%M"),
        "is_active": "on",
    }
    data.update(overrides)
    return data


def manage_urls(coupon):
    return [
        reverse("coupons:manage_coupons"),
        reverse("coupons:manage_coupon_create"),
        reverse("coupons:manage_coupon_update", kwargs={"pk": coupon.pk}),
    ]


# --- Access control ----------------------------------------------------------


def test_anonymous_users_are_sent_to_login(client, coupon):
    for url in manage_urls(coupon):
        response = client.get(url)

        assert response.status_code == HTTPStatus.FOUND, url
        assert reverse("accounts:login") in response.url


def test_customers_get_403(client, customer, coupon):
    client.force_login(customer)

    for url in manage_urls(coupon):
        assert client.get(url).status_code == HTTPStatus.FORBIDDEN, url


def test_staff_get_200(client, staff_user, coupon):
    client.force_login(staff_user)

    for url in manage_urls(coupon):
        assert client.get(url).status_code == HTTPStatus.OK, url


# --- CRUD ----------------------------------------------------------------


def test_staff_can_create_an_order_wide_coupon(client, staff_user):
    client.force_login(staff_user)

    response = client.post(
        reverse("coupons:manage_coupon_create"), coupon_data(), follow=True
    )

    coupon = Coupon.objects.get(code="SPRINGSALE")
    assert coupon.discount_type == Coupon.DiscountType.PERCENT
    assert coupon.is_order_wide
    assert "created." in response.content.decode()


def test_staff_can_create_a_product_scoped_coupon(client, staff_user, product):
    client.force_login(staff_user)

    client.post(
        reverse("coupons:manage_coupon_create"),
        coupon_data(products=[str(product.pk)]),
    )

    coupon = Coupon.objects.get(code="SPRINGSALE")
    assert list(coupon.products.all()) == [product]
    assert not coupon.is_order_wide


def test_staff_can_edit_a_coupon(client, staff_user, coupon):
    client.force_login(staff_user)
    data = coupon_data(code=coupon.code, discount_value="25.00")

    client.post(reverse("coupons:manage_coupon_update", kwargs={"pk": coupon.pk}), data)

    coupon.refresh_from_db()
    assert str(coupon.discount_value) == "25.00"


def test_percent_discount_over_100_is_rejected(client, staff_user):
    client.force_login(staff_user)

    response = client.post(
        reverse("coupons:manage_coupon_create"),
        coupon_data(discount_value="150.00"),
    )

    assert response.status_code == HTTPStatus.OK
    assert "cannot exceed 100" in response.content.decode()
    assert not Coupon.objects.exists()


def test_an_end_date_before_the_start_is_rejected(client, staff_user):
    client.force_login(staff_user)
    now = timezone.now()

    response = client.post(
        reverse("coupons:manage_coupon_create"),
        coupon_data(
            valid_from=now.strftime("%Y-%m-%dT%H:%M"),
            valid_until=(now - timedelta(days=1)).strftime("%Y-%m-%dT%H:%M"),
        ),
    )

    assert response.status_code == HTTPStatus.OK
    assert "must be after the start" in response.content.decode()
    assert not Coupon.objects.exists()


def test_code_must_be_unique(client, staff_user, coupon):
    client.force_login(staff_user)

    response = client.post(
        reverse("coupons:manage_coupon_create"), coupon_data(code=coupon.code)
    )

    assert response.status_code == HTTPStatus.OK
    assert "already exists" in response.content.decode()
    assert Coupon.objects.count() == 1


# --- Retire / reactivate ------------------------------------------------


def test_staff_can_retire_and_reactivate_a_coupon(client, staff_user, coupon):
    client.force_login(staff_user)
    toggle_url = reverse("coupons:manage_coupon_toggle", kwargs={"pk": coupon.pk})

    response = client.post(toggle_url, follow=True)
    coupon.refresh_from_db()
    assert not coupon.is_active
    assert "retired." in response.content.decode()

    response = client.post(toggle_url, follow=True)
    coupon.refresh_from_db()
    assert coupon.is_active
    assert "reactivated." in response.content.decode()


def test_retiring_a_coupon_does_not_touch_past_orders(
    client, staff_user, coupon, customer
):
    order = Order.objects.create(
        user=customer,
        total="629.98",
        coupon=coupon,
        coupon_code=coupon.code,
        discount_amount="70.00",
        email="casey@example.com",
        shipping_name="Casey Monroe",
        shipping_street="9 Synapse Court",
        shipping_city="Canyon",
        shipping_state="TX",
        shipping_zip="79015",
        billing_name="Casey Monroe",
        billing_street="9 Synapse Court",
        billing_city="Canyon",
        billing_state="TX",
        billing_zip="79015",
        card_last4="4242",
    )
    client.force_login(staff_user)

    client.post(reverse("coupons:manage_coupon_toggle", kwargs={"pk": coupon.pk}))

    order.refresh_from_db()
    assert order.coupon_code == "WELCOME10"
    assert str(order.discount_amount) == "70.00"
    assert str(order.total) == "629.98"


# --- List view -------------------------------------------------------------


def test_list_has_a_designed_empty_state(client, staff_user):
    client.force_login(staff_user)

    assert (
        "No coupons yet"
        in client.get(reverse("coupons:manage_coupons")).content.decode()
    )


def test_list_shows_scope_and_status(client, staff_user, coupon, product):
    client.force_login(staff_user)
    coupon.products.add(product)

    page = client.get(reverse("coupons:manage_coupons")).content.decode()

    assert coupon.code in page
    assert product.name in page
    assert "Active" in page
