import re
from datetime import timedelta

import pytest
from django.contrib import admin
from django.contrib.auth import get_user_model
from django.contrib.auth.models import AnonymousUser
from django.db import IntegrityError
from django.urls import reverse
from django.utils import timezone

from orders.models import Order, OrderItem

from .models import Review


@pytest.fixture
def other_customer(db):
    return get_user_model().objects.create_user(
        username="dana", first_name="Dana", last_name="Whitfield"
    )


def detail(client, product):
    return client.get(reverse("products:detail", kwargs={"slug": product.slug}))


# --- Model behavior ---------------------------------------------------------


def test_review_str(review):
    assert str(review) == "4★ Seraphine Home Hub by customer"


def test_one_review_per_user_and_product(review):
    with pytest.raises(IntegrityError):
        Review.objects.create(user=review.user, product=review.product, rating=2)


@pytest.mark.parametrize("rating", [0, 6])
def test_rating_must_be_one_to_five(customer, product, rating):
    with pytest.raises(IntegrityError):
        Review.objects.create(user=customer, product=product, rating=rating)


def test_deleting_the_product_deletes_its_reviews(review):
    review.product.delete()

    assert not Review.objects.exists()


def test_deleting_the_user_deletes_their_reviews(review):
    review.user.delete()

    assert not Review.objects.exists()


def test_reviewer_name_is_first_name_and_last_initial(other_customer, product):
    review = Review.objects.create(user=other_customer, product=product, rating=5)

    assert review.reviewer_name == "Dana W."


def test_reviewer_name_without_a_last_name_is_the_first_name(customer, product):
    customer.first_name = "Casey"
    review = Review.objects.create(user=customer, product=product, rating=5)

    assert review.reviewer_name == "Casey"


def test_reviewer_name_falls_back_to_the_username(review):
    assert review.reviewer_name == "customer"


def test_reviews_come_newest_first(review, other_customer):
    newer = Review.objects.create(user=other_customer, product=review.product, rating=2)
    Review.objects.filter(pk=review.pk).update(
        created_at=timezone.now() - timedelta(days=1)
    )

    assert list(Review.objects.all()) == [newer, review]


def test_can_review_only_a_signed_in_purchaser_who_has_not_reviewed(
    customer, other_customer, purchased_product
):
    assert not Review.can_review(AnonymousUser(), purchased_product)
    assert not Review.can_review(other_customer, purchased_product)
    assert Review.can_review(customer, purchased_product)

    Review.objects.create(user=customer, product=purchased_product, rating=5)

    assert not Review.can_review(customer, purchased_product)


def test_author_edit_changes_rating_and_comment_and_clears_the_staff_flag(review):
    Review.objects.filter(pk=review.pk).update(edited_by_staff=True)
    review.refresh_from_db()

    review.author_edit(rating=2, comment="Started answering my thoughts.")

    review.refresh_from_db()
    assert review.rating == 2
    assert review.comment == "Started answering my thoughts."
    assert not review.edited_by_staff


def test_can_change_is_for_the_author_and_staff_only(
    review, other_customer, staff_user
):
    assert review.can_change(review.user)
    assert review.can_change(staff_user)
    assert not review.can_change(other_customer)
    assert not review.can_change(AnonymousUser())


def test_review_is_registered_in_the_admin():
    assert admin.site.is_registered(Review)


@pytest.mark.django_db
def test_summary_gives_the_average_to_one_decimal_and_the_count(product):
    assert product.reviews.summary() == {"average": None, "count": 0}

    for username, rating in [("ana", 5), ("ben", 4), ("cy", 4)]:
        user = get_user_model().objects.create_user(username=username)
        Review.objects.create(user=user, product=product, rating=rating)

    assert product.reviews.summary() == {"average": 4.3, "count": 3}


def test_was_edited_only_after_a_later_update(customer, product):
    review = Review.objects.create(user=customer, product=product, rating=4)
    assert not review.was_edited

    # Posted an hour ago, changed now.
    Review.objects.filter(pk=review.pk).update(
        created_at=timezone.now() - timedelta(hours=1)
    )
    review.refresh_from_db()
    review.comment = "Better than I expected."
    review.save()

    assert review.was_edited


# --- The Reviews section on the product page ---------------------------------


def test_a_product_without_reviews_shows_the_empty_state(client, product):
    response = detail(client, product)

    assert "No reviews yet — be the first." in response.text


def test_the_summary_shows_the_average_and_count(client, review, other_customer):
    Review.objects.create(user=other_customer, product=review.product, rating=5)

    response = detail(client, review.product)

    assert "4.5 out of 5" in response.text
    assert "2 reviews" in response.text
    assert "No reviews yet" not in response.text


def test_each_review_shows_its_details(client, review):
    response = detail(client, review.product)

    assert "customer" in response.text
    assert "Verified purchase" in response.text
    assert 'aria-label="4 out of 5 stars"' in response.text
    assert "Hears me even when I whisper." in response.text
    assert review.created_at.strftime("%B") in response.text


def test_reviews_list_newest_first_on_the_page(client, review, other_customer):
    Review.objects.filter(pk=review.pk).update(
        created_at=timezone.now() - timedelta(days=1)
    )
    Review.objects.create(
        user=other_customer, product=review.product, rating=2, comment="Too nosy."
    )

    text = detail(client, review.product).text

    assert text.index("Too nosy.") < text.index("Hears me even when I whisper.")


def test_a_review_without_a_comment_still_shows(client, other_customer, product):
    Review.objects.create(user=other_customer, product=product, rating=3)

    response = detail(client, product)

    assert "Dana W." in response.text
    assert 'aria-label="3 out of 5 stars"' in response.text


def test_markers_show_only_when_applicable(client, review):
    text = detail(client, review.product).text
    assert "(edited)" not in text
    assert "Edited by staff" not in text

    Review.objects.filter(pk=review.pk).update(
        created_at=timezone.now() - timedelta(hours=1), edited_by_staff=True
    )

    text = detail(client, review.product).text
    assert "(edited)" in text
    assert "Edited by staff" in text


def test_anonymous_visitors_get_a_sign_in_link_back_to_the_product(client, product):
    response = detail(client, product)

    login = reverse("accounts:login")
    assert f'href="{login}?next=/products/seraphine-home-hub/"' in response.text
    assert "Sign in to review this product" in response.text


def test_signed_in_non_purchasers_get_the_purchasers_only_note(
    client, customer, product
):
    client.force_login(customer)

    response = detail(client, product)

    assert "Only customers who've purchased this product" in response.text
    assert "Sign in to review" not in response.text


def test_a_cancelled_order_does_not_count_as_a_purchase(
    client, customer, purchased_product
):
    customer.orders.update(status="CANCELLED")
    client.force_login(customer)

    response = detail(client, purchased_product)

    assert "Only customers who've purchased this product" in response.text


# --- Posting a review ---------------------------------------------------------


def create(client, product, **data):
    return client.post(reverse("reviews:create", kwargs={"pk": product.pk}), data)


@pytest.mark.parametrize("order_status", [None, "CANCELLED"])
def test_a_non_purchaser_cannot_create_a_review(
    client, customer, purchased_product, order_status
):
    # None: the customer never bought it; CANCELLED: their only order was cancelled.
    if order_status is None:
        customer.orders.all().delete()
    else:
        customer.orders.update(status=order_status)
    client.force_login(customer)

    response = create(client, purchased_product, rating=5, comment="Sneaky.")

    assert response.status_code == 403
    assert not Review.objects.exists()


def test_a_second_create_keeps_one_review_and_shows_it(
    client, customer, purchased_product
):
    client.force_login(customer)
    create(client, purchased_product, rating=4, comment="First tab.")

    response = create(client, purchased_product, rating=1, comment="Second tab.")

    assert response.status_code == 200
    review = Review.objects.get()
    assert (review.rating, review.comment) == (4, "First tab.")
    assert "First tab." in response.text
    assert "Second tab." not in response.text


def buy(user, product):
    """Put the product on a placed order for the user."""
    address = {
        f"{kind}_{field}": value
        for kind in ("shipping", "billing")
        for field, value in [
            ("name", "Pat Lee"),
            ("street", "1 Synapse Way"),
            ("city", "Canyon"),
            ("state", "TX"),
            ("zip", "79015"),
        ]
    }
    order = Order.objects.create(
        user=user,
        total=product.price,
        email="pat@example.com",
        card_last4="4242",
        **address,
    )
    OrderItem.objects.create(
        order=order,
        product=product,
        product_name=product.name,
        unit_price=product.price,
        quantity=1,
    )


def test_create_is_post_only(client, customer, purchased_product):
    client.force_login(customer)

    response = client.get(
        reverse("reviews:create", kwargs={"pk": purchased_product.pk})
    )

    assert response.status_code == 405


def test_create_redirects_anonymous_visitors_to_sign_in(client, product):
    response = create(client, product, rating=5)

    assert response.status_code == 302
    assert response.url.startswith(reverse("accounts:login"))
    assert not Review.objects.exists()


def test_create_404s_on_a_missing_product(client, customer):
    client.force_login(customer)

    response = client.post(reverse("reviews:create", kwargs={"pk": 999}), {})

    assert response.status_code == 404


def test_a_purchaser_posts_a_review_and_sees_it_pinned(
    client, customer, other_customer, purchased_product
):
    Review.objects.create(
        user=other_customer, product=purchased_product, rating=2, comment="Meh."
    )
    client.force_login(customer)

    response = create(client, purchased_product, rating=5, comment="Love it.")

    review = Review.objects.get(user=customer)
    assert (review.rating, review.comment) == (5, "Love it.")
    text = response.text
    assert 'id="reviews"' in text
    assert "<html" not in text
    # Pinned in "Your review", above everyone else's reviews.
    assert text.index("Your review") < text.index("Love it.") < text.index("Meh.")
    assert "Post review" not in text
    assert "3.5 out of 5" in text
    assert "2 reviews" in text


def test_the_comment_is_optional(client, customer, purchased_product):
    client.force_login(customer)

    create(client, purchased_product, rating=3)

    assert Review.objects.get().comment == ""


def test_a_purchaser_can_review_an_unavailable_product(
    client, customer, unavailable_product
):
    buy(customer, unavailable_product)
    client.force_login(customer)

    create(client, unavailable_product, rating=4)

    assert Review.objects.filter(product=unavailable_product).exists()


@pytest.mark.parametrize(
    "data, error",
    [
        ({"comment": "Forgot the stars."}, "Choose a star rating."),
        ({"rating": 0, "comment": "Forgot the stars."}, "Select a valid choice."),
        ({"rating": 6, "comment": "Forgot the stars."}, "Select a valid choice."),
    ],
)
def test_the_rating_is_required_and_one_to_five(
    client, customer, purchased_product, data, error
):
    client.force_login(customer)

    response = create(client, purchased_product, **data)

    assert response.status_code == 200
    assert not Review.objects.exists()
    assert error in response.text
    assert "Forgot the stars." in response.text  # input preserved


def test_a_too_long_comment_is_rejected_with_the_input_kept(
    client, customer, purchased_product
):
    client.force_login(customer)

    response = create(client, purchased_product, rating=4, comment="x" * 2001)

    assert not Review.objects.exists()
    assert "at most 2000 characters" in response.text
    assert "x" * 2001 in response.text
    assert re.search(r'value="4"[^>]*checked', response.text)  # stars kept too
    assert not re.search(r'value="[1235]"[^>]*checked', response.text)


def test_staff_follow_the_same_purchase_rule(client, staff_user, product):
    client.force_login(staff_user)

    assert create(client, product, rating=5).status_code == 403

    buy(staff_user, product)
    create(client, product, rating=5)

    assert Review.objects.filter(user=staff_user).exists()


def test_an_eligible_customer_sees_the_empty_form(client, customer, purchased_product):
    client.force_login(customer)

    response = detail(client, purchased_product)

    create_url = reverse("reviews:create", kwargs={"pk": purchased_product.pk})
    assert f'hx-post="{create_url}"' in response.text
    assert 'name="rating"' in response.text
    assert "Post review" in response.text
    assert "Only customers who've purchased" not in response.text


def test_the_section_view_renders_only_the_partial(client, review):
    response = client.get(reverse("reviews:section", kwargs={"pk": review.product.pk}))

    assert response.status_code == 200
    assert 'id="reviews"' in response.text
    assert "Hears me even when I whisper." in response.text
    assert "<html" not in response.text


def test_the_section_view_404s_on_a_missing_product(client, db):
    response = client.get(reverse("reviews:section", kwargs={"pk": 999}))

    assert response.status_code == 404


# --- Editing a review ----------------------------------------------------------


def edit(client, review, **data):
    return client.post(reverse("reviews:edit", kwargs={"pk": review.pk}), data)


def test_an_author_edit_saves_and_shows_edited_even_after_cancelling(client, review):
    # Posted an hour ago; the order it was bought on has since been cancelled.
    Review.objects.filter(pk=review.pk).update(
        created_at=timezone.now() - timedelta(hours=1)
    )
    review.user.orders.update(status="CANCELLED")
    client.force_login(review.user)

    response = edit(client, review, rating=2, comment="Started finishing my sentences.")

    review.refresh_from_db()
    assert (review.rating, review.comment) == (2, "Started finishing my sentences.")
    assert response.status_code == 200
    assert "Started finishing my sentences." in response.text
    assert "Hears me even when I whisper." not in response.text
    assert "(edited)" in response.text
    assert "2.0 out of 5" in response.text


def test_another_customer_cannot_edit_a_review(client, review, other_customer):
    client.force_login(other_customer)
    edit_url = reverse("reviews:edit", kwargs={"pk": review.pk})

    assert client.get(edit_url).status_code == 403
    assert edit(client, review, rating=1, comment="Hijacked.").status_code == 403

    review.refresh_from_db()
    assert (review.rating, review.comment) == (4, "Hears me even when I whisper.")


def test_the_edit_form_comes_pre_filled_in_place(client, review):
    client.force_login(review.user)

    response = client.get(reverse("reviews:edit", kwargs={"pk": review.pk}))

    text = response.text
    assert response.status_code == 200
    assert 'id="reviews"' in text
    assert "<html" not in text
    edit_url = reverse("reviews:edit", kwargs={"pk": review.pk})
    section_url = reverse("reviews:section", kwargs={"pk": review.product.pk})
    assert f'hx-post="{edit_url}"' in text
    assert f'hx-get="{section_url}"' in text  # Cancel
    assert "Save changes" in text
    assert ">Hears me even when I whisper.</textarea>" in text
    assert re.search(r'value="4"[^>]*checked', text)
    assert not re.search(r'value="[1235]"[^>]*checked', text)


@pytest.mark.parametrize(
    "data, error",
    [
        ({"comment": "No stars this time."}, "Choose a star rating."),
        ({"rating": 2, "comment": "x" * 2001}, "at most 2000 characters"),
    ],
)
def test_an_invalid_edit_keeps_the_input_and_the_review(client, review, data, error):
    client.force_login(review.user)

    response = edit(client, review, **data)

    assert response.status_code == 200
    assert error in response.text
    assert data["comment"] in response.text
    assert "Save changes" in response.text  # still the edit form
    review.refresh_from_db()
    assert (review.rating, review.comment) == (4, "Hears me even when I whisper.")


def test_cancel_returns_the_review_unchanged(client, review):
    client.force_login(review.user)
    client.get(reverse("reviews:edit", kwargs={"pk": review.pk}))

    response = client.get(reverse("reviews:section", kwargs={"pk": review.product.pk}))

    assert "Hears me even when I whisper." in response.text
    assert 'aria-label="4 out of 5 stars"' in response.text
    assert "Save changes" not in response.text
    assert "(edited)" not in response.text


@pytest.mark.parametrize("method", ["get", "post"])
def test_edit_redirects_anonymous_visitors_to_sign_in(client, review, method):
    response = getattr(client, method)(
        reverse("reviews:edit", kwargs={"pk": review.pk})
    )

    assert response.status_code == 302
    assert response.url.startswith(reverse("accounts:login"))


@pytest.mark.parametrize("method", ["get", "post"])
def test_edit_404s_on_a_missing_review(client, customer, method):
    client.force_login(customer)

    response = getattr(client, method)(reverse("reviews:edit", kwargs={"pk": 999}))

    assert response.status_code == 404


def test_only_the_author_sees_the_edit_button(client, review, other_customer):
    edit_url = reverse("reviews:edit", kwargs={"pk": review.pk})
    client.force_login(review.user)
    assert f'hx-get="{edit_url}"' in detail(client, review.product).text

    client.force_login(other_customer)
    assert f'hx-get="{edit_url}"' not in detail(client, review.product).text


# --- Deleting a review ---------------------------------------------------------


def delete(client, review):
    return client.post(reverse("reviews:delete", kwargs={"pk": review.pk}))


def test_the_author_deletes_their_review_and_gets_the_empty_form_back(client, review):
    client.force_login(review.user)

    response = delete(client, review)

    assert not Review.objects.filter(pk=review.pk).exists()
    assert response.status_code == 200
    assert "<html" not in response.text
    assert "Hears me even when I whisper." not in response.text
    assert "No reviews yet — be the first." in response.text
    create_url = reverse("reviews:create", kwargs={"pk": review.product.pk})
    assert f'hx-post="{create_url}"' in response.text
    assert "Post review" in response.text


def test_another_customer_cannot_delete_a_review(client, review, other_customer):
    client.force_login(other_customer)

    response = delete(client, review)

    assert response.status_code == 403
    assert Review.objects.filter(pk=review.pk).exists()


def test_staff_can_delete_any_review(client, review, other_customer, staff_user):
    Review.objects.create(user=other_customer, product=review.product, rating=2)
    client.force_login(staff_user)

    response = delete(client, review)

    assert response.status_code == 200
    assert not Review.objects.filter(pk=review.pk).exists()
    assert "Hears me even when I whisper." not in response.text
    assert "2.0 out of 5" in response.text
    assert "1 review<" in response.text


def test_delete_is_post_only(client, review):
    client.force_login(review.user)

    response = client.get(reverse("reviews:delete", kwargs={"pk": review.pk}))

    assert response.status_code == 405
    assert Review.objects.filter(pk=review.pk).exists()


def test_delete_redirects_anonymous_visitors_to_sign_in(client, review):
    response = delete(client, review)

    assert response.status_code == 302
    assert response.url.startswith(reverse("accounts:login"))
    assert Review.objects.filter(pk=review.pk).exists()


def test_delete_404s_on_a_missing_review(client, customer):
    client.force_login(customer)

    response = client.post(reverse("reviews:delete", kwargs={"pk": 999}))

    assert response.status_code == 404


def test_delete_buttons_show_only_to_those_allowed_and_ask_first(
    client, review, other_customer, staff_user
):
    other_review = Review.objects.create(
        user=other_customer, product=review.product, rating=2
    )
    button = 'hx-post="{}"[^>]*hx-confirm="Delete this review\\?"'

    def delete_buttons(user):
        client.force_login(user)
        text = detail(client, review.product).text
        return {
            r.pk
            for r in (review, other_review)
            if re.search(
                button.format(reverse("reviews:delete", kwargs={"pk": r.pk})), text
            )
        }

    assert delete_buttons(review.user) == {review.pk}
    assert delete_buttons(other_customer) == {other_review.pk}
    assert delete_buttons(staff_user) == {review.pk, other_review.pk}


def test_the_catalog_grid_is_unchanged(client, review):
    response = client.get(reverse("products:catalog"))

    assert "Verified purchase" not in response.text
    assert "out of 5" not in response.text
