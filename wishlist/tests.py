from datetime import timedelta
from decimal import Decimal
from http import HTTPStatus

import pytest
from django.contrib import admin
from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.db import IntegrityError, connection
from django.test.utils import CaptureQueriesContext
from django.urls import reverse

from products.models import Product

from .models import Wishlist, WishlistItem

# --- Model behavior ---------------------------------------------------------


def test_wishlist_str(wishlist):
    assert str(wishlist) == "Wishlist for customer"


def test_for_user_creates_the_wishlist_once(customer):
    first = Wishlist.for_user(customer)
    second = Wishlist.for_user(customer)

    assert first == second
    assert Wishlist.objects.count() == 1


def test_each_user_gets_their_own_wishlist(customer, staff_user):
    assert Wishlist.for_user(customer) != Wishlist.for_user(staff_user)
    assert Wishlist.objects.count() == 2


def test_add_saves_the_product(wishlist, product):
    item = wishlist.add(product)

    assert item.product == product
    assert wishlist.items.count() == 1


def test_repeat_add_keeps_a_single_entry(wishlist, product):
    first = wishlist.add(product)
    second = wishlist.add(product)

    assert first == second
    assert wishlist.items.count() == 1


def test_unavailable_product_can_be_saved(wishlist, unavailable_product):
    wishlist.add(unavailable_product)

    assert wishlist.contains(unavailable_product)


def test_contains(wishlist, product, unavailable_product):
    wishlist.add(product)

    assert wishlist.contains(product)
    assert not wishlist.contains(unavailable_product)


def test_remove_deletes_a_saved_product_and_ignores_an_unsaved_one(
    wishlist, product, unavailable_product
):
    wishlist.add(product)

    wishlist.remove(product)
    wishlist.remove(unavailable_product)

    assert not wishlist.contains(product)
    assert not wishlist.items.exists()


def test_wishlist_product_pair_is_unique(wishlist, product):
    wishlist.add(product)

    with pytest.raises(IntegrityError):
        WishlistItem.objects.create(wishlist=wishlist, product=product)


def test_deleting_a_product_deletes_its_wishlist_items(wishlist, product):
    wishlist.add(product)

    product.delete()

    assert not WishlistItem.objects.exists()


def test_deleting_a_user_deletes_their_wishlist(customer, wishlist, product):
    wishlist.add(product)

    customer.delete()

    assert not Wishlist.objects.exists()
    assert not WishlistItem.objects.exists()


def test_wishlist_models_are_not_in_the_admin():
    assert not admin.site.is_registered(Wishlist)
    assert not admin.site.is_registered(WishlistItem)


# --- Adding (HTMX) -----------------------------------------------------------


def test_add_requires_login(client, product):
    response = client.post(reverse("wishlist:add", args=[product.pk]))

    assert response.status_code == HTTPStatus.FOUND
    assert reverse("accounts:login") in response.url
    assert not WishlistItem.objects.exists()


def test_add_is_post_only(client, customer, product):
    client.force_login(customer)

    response = client.get(reverse("wishlist:add", args=[product.pk]))

    assert response.status_code == HTTPStatus.METHOD_NOT_ALLOWED


def test_add_missing_product_is_404(client, customer):
    client.force_login(customer)

    response = client.post(reverse("wishlist:add", args=[9999]))

    assert response.status_code == HTTPStatus.NOT_FOUND


def test_add_saves_and_renders_the_saved_button(client, customer, product):
    client.force_login(customer)

    response = client.post(reverse("wishlist:add", args=[product.pk]))

    assert response.status_code == HTTPStatus.OK
    assert Wishlist.for_user(customer).contains(product)
    page = response.content.decode()
    assert "On your wishlist" in page
    assert "<html" not in page


def test_add_unavailable_product(client, customer, unavailable_product):
    client.force_login(customer)

    response = client.post(reverse("wishlist:add", args=[unavailable_product.pk]))

    assert response.status_code == HTTPStatus.OK
    assert Wishlist.for_user(customer).contains(unavailable_product)


def test_repeat_add_request_keeps_one_entry(client, customer, product):
    client.force_login(customer)

    client.post(reverse("wishlist:add", args=[product.pk]))
    response = client.post(reverse("wishlist:add", args=[product.pk]))

    assert "On your wishlist" in response.content.decode()
    assert Wishlist.for_user(customer).items.count() == 1


def test_one_users_add_never_touches_another_wishlist(client, customer, product):
    other = get_user_model().objects.create_user(username="other", password="pw")
    other_wishlist = Wishlist.for_user(other)
    client.force_login(customer)

    client.post(reverse("wishlist:add", args=[product.pk]))

    assert Wishlist.for_user(customer).contains(product)
    assert not other_wishlist.items.exists()


def test_staff_get_their_own_wishlist(client, staff_user, customer, product):
    client.force_login(staff_user)

    client.post(reverse("wishlist:add", args=[product.pk]))

    assert Wishlist.for_user(staff_user).contains(product)
    assert not Wishlist.for_user(customer).contains(product)


# --- Removing (HTMX) ---------------------------------------------------------


def test_remove_requires_login(client, wishlist, product):
    wishlist.add(product)

    response = client.post(reverse("wishlist:remove", args=[product.pk]))

    assert response.status_code == HTTPStatus.FOUND
    assert reverse("accounts:login") in response.url
    assert wishlist.contains(product)


def test_remove_is_post_only(client, customer, wishlist, product):
    wishlist.add(product)
    client.force_login(customer)

    response = client.get(reverse("wishlist:remove", args=[product.pk]))

    assert response.status_code == HTTPStatus.METHOD_NOT_ALLOWED
    assert wishlist.contains(product)


def test_remove_missing_product_is_404(client, customer):
    client.force_login(customer)

    response = client.post(reverse("wishlist:remove", args=[9999]))

    assert response.status_code == HTTPStatus.NOT_FOUND


def test_remove_unavailable_product(client, customer, wishlist, unavailable_product):
    wishlist.add(unavailable_product)
    client.force_login(customer)

    response = client.post(reverse("wishlist:remove", args=[unavailable_product.pk]))

    assert response.status_code == HTTPStatus.OK
    assert not wishlist.contains(unavailable_product)


def test_one_users_remove_never_touches_another_wishlist(
    client, customer, wishlist, product
):
    other = get_user_model().objects.create_user(username="other", password="pw")
    other_wishlist = Wishlist.for_user(other)
    other_wishlist.add(product)
    wishlist.add(product)
    client.force_login(customer)

    client.post(reverse("wishlist:remove", args=[product.pk]))

    assert not wishlist.contains(product)
    assert other_wishlist.contains(product)


def test_add_then_remove_redraws_each_true_state(client, customer, product):
    client.force_login(customer)

    added = client.post(reverse("wishlist:add", args=[product.pk]))
    removed = client.post(reverse("wishlist:remove", args=[product.pk]))

    assert reverse("wishlist:remove", args=[product.pk]) in added.content.decode()
    assert reverse("wishlist:add", args=[product.pk]) in removed.content.decode()


def test_repeat_remove_request_leaves_it_removed(client, customer, wishlist, product):
    wishlist.add(product)
    client.force_login(customer)

    first = client.post(reverse("wishlist:remove", args=[product.pk]))
    second = client.post(reverse("wishlist:remove", args=[product.pk]))

    assert not wishlist.contains(product)
    for response in (first, second):
        assert response.status_code == HTTPStatus.OK
        page = response.content.decode()
        assert "Add to wishlist" in page
        assert reverse("wishlist:add", args=[product.pk]) in page
        assert "<html" not in page


# --- The detail-page button --------------------------------------------------


def test_detail_shows_add_button_when_unsaved(client, customer, product):
    client.force_login(customer)

    response = client.get(product.get_absolute_url())

    page = response.content.decode()
    assert "Add to wishlist" in page
    assert reverse("wishlist:add", args=[product.pk]) in page


def test_detail_shows_saved_state_when_saved(client, customer, wishlist, product):
    wishlist.add(product)
    client.force_login(customer)

    response = client.get(product.get_absolute_url())

    page = response.content.decode()
    assert "On your wishlist" in page
    assert reverse("wishlist:add", args=[product.pk]) not in page


def test_detail_saved_button_posts_to_remove(client, customer, wishlist, product):
    wishlist.add(product)
    client.force_login(customer)

    response = client.get(product.get_absolute_url())

    page = response.content.decode()
    assert "On your wishlist — remove" in page
    assert f'hx-post="{reverse("wishlist:remove", args=[product.pk])}"' in page


def test_detail_shows_sign_in_link_to_visitors(client, product):
    response = client.get(product.get_absolute_url())

    page = response.content.decode()
    assert "Add to wishlist" in page
    assert reverse("wishlist:add", args=[product.pk]) not in page
    assert f"{reverse('accounts:login')}?next={product.get_absolute_url()}" in page


def test_detail_offers_wishlist_for_unavailable_product(
    client, customer, unavailable_product
):
    client.force_login(customer)

    response = client.get(unavailable_product.get_absolute_url())

    assert reverse("wishlist:add", args=[unavailable_product.pk]) in (
        response.content.decode()
    )


def test_catalog_grid_has_no_wishlist_button(client, customer, product):
    client.force_login(customer)

    response = client.get(reverse("products:catalog"))

    page = response.content.decode()
    assert product.name in page
    assert "Add to wishlist" not in page


# --- The wishlist page -------------------------------------------------------


def test_page_lists_only_my_items_newest_first(
    client, customer, wishlist, product, unavailable_product, category
):
    older = wishlist.add(product)
    newer = wishlist.add(unavailable_product)
    WishlistItem.objects.filter(pk=older.pk).update(
        added_at=newer.added_at - timedelta(days=1)
    )
    others_only = Product.objects.create(
        name="Someone Else's Gadget",
        slug="someone-elses-gadget",
        price=Decimal("10.00"),
        category=category,
    )
    other = get_user_model().objects.create_user(username="other", password="pw")
    Wishlist.for_user(other).add(others_only)
    client.force_login(customer)

    response = client.get(reverse("wishlist:detail"))

    page = response.content.decode()
    assert response.status_code == HTTPStatus.OK
    assert unavailable_product.name in page
    assert product.name in page
    assert page.index(unavailable_product.name) < page.index(product.name)
    assert others_only.name not in page


def test_page_marks_only_unavailable_products(
    client, customer, wishlist, product, unavailable_product
):
    wishlist.add(product)
    wishlist.add(unavailable_product)
    client.force_login(customer)

    response = client.get(reverse("wishlist:detail"))

    page = response.content.decode()
    assert page.count("Unavailable") == 1
    unavailable_row = page[page.index(unavailable_product.name) :]
    available_row = page[page.index(product.name) :]
    assert "Unavailable" in unavailable_row
    assert "Unavailable" not in available_row


def test_page_query_count_does_not_grow_with_items(
    client, customer, wishlist, product, category
):
    wishlist.add(product)
    client.force_login(customer)
    url = reverse("wishlist:detail")
    with CaptureQueriesContext(connection) as one_item:
        client.get(url)

    for n in range(3):
        wishlist.add(
            Product.objects.create(
                name=f"Gadget {n}",
                slug=f"gadget-{n}",
                price=Decimal("10.00"),
                category=category,
            )
        )
    with CaptureQueriesContext(connection) as four_items:
        client.get(url)

    assert len(four_items) == len(one_item)


def test_page_requires_login(client):
    response = client.get(reverse("wishlist:detail"))

    assert response.status_code == HTTPStatus.FOUND
    assert reverse("accounts:login") in response.url


def test_page_row_shows_image_linked_name_and_price(
    client, customer, wishlist, product
):
    wishlist.add(product)
    client.force_login(customer)

    response = client.get(reverse("wishlist:detail"))

    page = response.content.decode()
    assert f'href="{product.get_absolute_url()}"' in page
    assert product.display_image_url in page
    assert "$349.99" in page


def test_page_drops_a_deleted_product(client, customer, wishlist, product):
    wishlist.add(product)
    product.delete()
    client.force_login(customer)

    response = client.get(reverse("wishlist:detail"))

    page = response.content.decode()
    assert product.name not in page
    assert "Your wishlist is empty" in page


def test_empty_wishlist_shows_the_empty_state(client, customer):
    client.force_login(customer)

    response = client.get(reverse("wishlist:detail"))

    page = response.content.decode()
    assert "Your wishlist is empty" in page
    assert f'href="{reverse("products:catalog")}"' in page


def test_navbar_links_to_wishlist_when_signed_in(client, customer):
    client.force_login(customer)

    response = client.get(reverse("products:catalog"))

    assert f'href="{reverse("wishlist:detail")}"' in response.content.decode()


def test_navbar_hides_wishlist_link_from_visitors(client, db):
    response = client.get(reverse("products:catalog"))

    assert f'href="{reverse("wishlist:detail")}"' not in response.content.decode()


# --- Removing from the wishlist page (HTMX) ----------------------------------


def test_remove_item_returns_the_list_without_it(
    client, customer, wishlist, product, unavailable_product
):
    wishlist.add(product)
    wishlist.add(unavailable_product)
    client.force_login(customer)

    response = client.post(reverse("wishlist:remove_item", args=[product.pk]))

    page = response.content.decode()
    assert response.status_code == HTTPStatus.OK
    assert product.name not in page
    assert unavailable_product.name in page
    assert "<html" not in page
    assert not wishlist.contains(product)


def test_remove_item_never_touches_another_users_wishlist(
    client, customer, wishlist, product
):
    other = get_user_model().objects.create_user(username="other", password="pw")
    other_wishlist = Wishlist.for_user(other)
    other_wishlist.add(product)
    client.force_login(customer)

    response = client.post(reverse("wishlist:remove_item", args=[product.pk]))

    assert response.status_code == HTTPStatus.OK
    assert other_wishlist.contains(product)
    assert product.name not in response.content.decode()


def test_remove_item_requires_login(client, wishlist, product):
    wishlist.add(product)

    response = client.post(reverse("wishlist:remove_item", args=[product.pk]))

    assert response.status_code == HTTPStatus.FOUND
    assert reverse("accounts:login") in response.url
    assert wishlist.contains(product)


def test_remove_item_is_post_only(client, customer, wishlist, product):
    wishlist.add(product)
    client.force_login(customer)

    response = client.get(reverse("wishlist:remove_item", args=[product.pk]))

    assert response.status_code == HTTPStatus.METHOD_NOT_ALLOWED
    assert wishlist.contains(product)


def test_removing_the_last_item_returns_the_empty_state(
    client, customer, wishlist, product
):
    wishlist.add(product)
    client.force_login(customer)

    response = client.post(reverse("wishlist:remove_item", args=[product.pk]))

    page = response.content.decode()
    assert "Your wishlist is empty" in page
    assert "<html" not in page


def test_page_rows_have_a_remove_button_targeting_the_list(
    client, customer, wishlist, product
):
    wishlist.add(product)
    client.force_login(customer)

    response = client.get(reverse("wishlist:detail"))

    page = response.content.decode()
    assert f'hx-post="{reverse("wishlist:remove_item", args=[product.pk])}"' in page
    assert 'hx-target="#wishlist-items"' in page
    assert 'id="wishlist-items"' in page


# --- The seed command --------------------------------------------------------


def test_seed_gives_customer_a_wishlist_with_an_unavailable_product(db):
    call_command("seed")

    customer = get_user_model().objects.get(username="customer")
    products = [item.product for item in Wishlist.for_user(customer).items.all()]
    assert 2 <= len(products) <= 3
    assert any(not product.is_available for product in products)


def test_reseeding_rebuilds_the_same_wishlist(db):
    call_command("seed")
    first = list(
        WishlistItem.objects.values_list("wishlist__user__username", "product__slug")
    )

    call_command("seed")
    second = list(
        WishlistItem.objects.values_list("wishlist__user__username", "product__slug")
    )

    assert first == second
    assert Wishlist.objects.count() == 1
