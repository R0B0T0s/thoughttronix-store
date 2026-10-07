from http import HTTPStatus

import pytest
from django.contrib.auth import authenticate, get_user_model
from django.db import IntegrityError, transaction
from django.urls import reverse

# --- Signup -----------------------------------------------------------------


def test_signup_page_returns_200(client, db):
    response = client.get(reverse("accounts:signup"))

    assert response.status_code == HTTPStatus.OK


def signup_data(**overrides):
    return {
        "username": "fresh-thinker",
        "email": "fresh@example.com",
        "password1": "neural-implant-9000",
        "password2": "neural-implant-9000",
        **overrides,
    }


def test_signup_creates_plain_customer(client, db):
    response = client.post(reverse("accounts:signup"), signup_data(), follow=True)

    user = get_user_model().objects.get(username="fresh-thinker")
    assert not user.is_staff
    assert not user.is_superuser

    # Signup hands off to the login page with a confirmation message;
    # auto-login is a student exercise, so the visitor is still anonymous.
    assert response.redirect_chain[-1][0] == reverse("accounts:login")
    assert "Account created" in response.content.decode()
    assert not response.context["user"].is_authenticated


def test_signup_password_mismatch_shows_field_error(client, db):
    response = client.post(
        reverse("accounts:signup"), signup_data(password2="neural-implant-9001")
    )

    assert response.status_code == HTTPStatus.OK
    assert response.context["form"].errors["password2"]
    assert not get_user_model().objects.filter(username="fresh-thinker").exists()


def test_signup_page_shows_email_field(client, db):
    response = client.get(reverse("accounts:signup"))

    assert 'name="email"' in response.content.decode()
    assert response.context["form"].fields["email"].required


def test_signup_without_email_is_rejected(client, db):
    response = client.post(reverse("accounts:signup"), signup_data(email=""))

    assert response.status_code == HTTPStatus.OK
    assert response.context["form"].errors["email"]
    assert not get_user_model().objects.filter(username="fresh-thinker").exists()


@pytest.mark.parametrize("taken", ["fresh@example.com", "Fresh@Example.COM"])
def test_signup_rejects_email_already_in_use(client, db, taken):
    get_user_model().objects.create_user(
        username="ada", email="fresh@example.com", password="x"
    )

    response = client.post(reverse("accounts:signup"), signup_data(email=taken))

    assert response.status_code == HTTPStatus.OK
    assert response.context["form"].errors["email"] == [
        "An account with that email already exists."
    ]
    assert not get_user_model().objects.filter(username="fresh-thinker").exists()


def test_signup_stores_normalized_email(client, db):
    client.post(reverse("accounts:signup"), signup_data(email="Fresh@EXAMPLE.com"))

    user = get_user_model().objects.get(username="fresh-thinker")
    assert user.email == "Fresh@example.com"


def test_signup_rejects_password_too_similar_to_email(client, db):
    response = client.post(
        reverse("accounts:signup"),
        signup_data(
            email="quantumthinker@example.com",
            password1="quantumthinker",
            password2="quantumthinker",
        ),
    )

    assert response.status_code == HTTPStatus.OK
    assert "too similar to the email address" in str(
        response.context["form"].errors["password2"]
    )
    assert not get_user_model().objects.filter(username="fresh-thinker").exists()


# --- The email constraint ----------------------------------------------------


def test_users_with_blank_emails_can_coexist(db):
    User = get_user_model()
    User.objects.create_user(username="legacy-one", password="x")
    User.objects.create_user(username="legacy-two", password="x")

    assert User.objects.filter(email="").count() == 2


def test_database_rejects_case_insensitive_duplicate_email(db):
    User = get_user_model()
    User.objects.create_user(username="ada", email="ada@example.com", password="x")

    with pytest.raises(IntegrityError), transaction.atomic():
        User.objects.create_user(
            username="ada-two", email="ADA@example.com", password="x"
        )


# --- Login and logout --------------------------------------------------------


def test_login_page_returns_200(client, db):
    response = client.get(reverse("accounts:login"))

    assert response.status_code == HTTPStatus.OK


def test_login_round_trip(client, customer):
    response = client.post(
        reverse("accounts:login"),
        {"username": "customer", "password": "customer123"},
        follow=True,
    )

    assert response.redirect_chain[-1][0] == reverse("products:catalog")
    assert response.context["user"] == customer


def test_login_bad_credentials_stays_put(client, customer):
    response = client.post(
        reverse("accounts:login"),
        {"username": "customer", "password": "wrong"},
    )

    assert response.status_code == HTTPStatus.OK
    assert response.context["form"].non_field_errors()


# --- Sign in with username or email -------------------------------------------


@pytest.fixture
def ada(db):
    return get_user_model().objects.create_user(
        username="ada", email="Ada@example.com", password="analytical-engine-1843"
    )


def sign_in(client, identifier, password):
    return client.post(
        reverse("accounts:login"), {"username": identifier, "password": password}
    )


@pytest.mark.parametrize(
    "identifier", ["ada", "Ada@example.com", "ada@example.com", "ADA@EXAMPLE.COM"]
)
def test_sign_in_by_username_or_email_in_any_case(client, ada, identifier):
    response = sign_in(client, identifier, "analytical-engine-1843")

    assert response.status_code == HTTPStatus.FOUND
    assert int(client.session["_auth_user_id"]) == ada.pk


@pytest.mark.parametrize("identifier", ["ada", "ada@example.com"])
def test_sign_in_wrong_password_fails_by_either_route(client, ada, identifier):
    response = sign_in(client, identifier, "difference-engine")

    assert response.status_code == HTTPStatus.OK
    assert response.context["form"].non_field_errors()
    assert "_auth_user_id" not in client.session


@pytest.mark.parametrize("identifier", ["ada", "ada@example.com"])
def test_inactive_user_cannot_sign_in_by_either_route(client, ada, identifier):
    ada.is_active = False
    ada.save()

    response = sign_in(client, identifier, "analytical-engine-1843")

    assert response.status_code == HTTPStatus.OK
    assert "_auth_user_id" not in client.session


def test_blank_email_user_signs_in_by_username(client, customer):
    response = sign_in(client, "customer", "customer123")

    assert response.status_code == HTTPStatus.FOUND
    assert int(client.session["_auth_user_id"]) == customer.pk


def test_blank_identifier_never_matches_blank_email_account(customer):
    assert authenticate(username="", password="customer123") is None


def test_username_match_wins_over_another_users_email(client, ada):
    # A username that happens to look like someone else's email.
    impostor = get_user_model().objects.create_user(
        username="ada@example.com", password="impostor-pass-77"
    )

    response = sign_in(client, "ada@example.com", "impostor-pass-77")

    assert response.status_code == HTTPStatus.FOUND
    assert int(client.session["_auth_user_id"]) == impostor.pk


def test_sign_in_label_mentions_email(client, db):
    response = client.get(reverse("accounts:login"))

    assert response.context["form"].fields["username"].label == "Username or email"
    assert "Username or email" in response.content.decode()


def test_logout_signs_out_with_message(client, customer):
    client.force_login(customer)

    response = client.post(reverse("accounts:logout"), follow=True)

    assert response.redirect_chain[-1][0] == reverse("products:catalog")
    assert "You have signed out." in response.content.decode()
    assert not response.context["user"].is_authenticated


# --- Auth-aware navbar --------------------------------------------------------


def test_navbar_offers_login_and_signup_to_visitors(client, db):
    page = client.get(reverse("products:catalog")).content.decode()

    assert reverse("accounts:login") in page
    assert reverse("accounts:signup") in page
    assert "Sign out" not in page


def test_navbar_greets_signed_in_customer(client, customer):
    client.force_login(customer)

    page = client.get(reverse("products:catalog")).content.decode()

    assert "Hi, customer" in page
    assert "Sign out" in page
    assert reverse("accounts:signup") not in page
