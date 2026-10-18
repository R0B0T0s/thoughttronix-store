from datetime import timedelta

import pytest
from django.contrib import admin
from django.contrib.auth import get_user_model
from django.db import IntegrityError
from django.urls import reverse
from django.utils import timezone

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


def test_the_catalog_grid_is_unchanged(client, review):
    response = client.get(reverse("products:catalog"))

    assert "Verified purchase" not in response.text
    assert "out of 5" not in response.text
