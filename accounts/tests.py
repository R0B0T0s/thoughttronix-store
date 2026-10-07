import io
import re
from datetime import datetime, timedelta
from http import HTTPStatus

import pytest
from django.contrib.auth import authenticate, get_user_model
from django.contrib.auth.tokens import PasswordResetTokenGenerator
from django.db import IntegrityError, transaction
from django.test import Client
from django.urls import reverse

from config.mail import ReadableConsoleEmailBackend

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


# --- The Account page and change email ----------------------------------------


@pytest.mark.parametrize(
    "name", ["accounts:account", "accounts:email_change", "accounts:password_change"]
)
def test_account_pages_redirect_anonymous_to_login(client, db, name):
    url = reverse(name)

    response = client.get(url)

    assert response.status_code == HTTPStatus.FOUND
    assert response.url == f"{reverse('accounts:login')}?next={url}"


def test_account_page_shows_current_email(client, ada):
    client.force_login(ada)

    page = client.get(reverse("accounts:account")).content.decode()

    assert "Ada@example.com" in page
    assert "Change email" in page
    assert reverse("accounts:email_change") in page


def test_account_page_prompts_blank_email_user_to_add_one(client, customer):
    client.force_login(customer)

    page = client.get(reverse("accounts:account")).content.decode()

    assert "Add an email" in page
    assert reverse("accounts:email_change") in page


def change_email(client, email, password):
    return client.post(
        reverse("accounts:email_change"),
        {"email": email, "current_password": password},
        follow=True,
    )


def test_email_change_wrong_password_leaves_email_untouched(client, ada, mailoutbox):
    client.force_login(ada)

    response = change_email(client, "lovelace@example.com", "difference-engine")

    assert response.context["form"].errors["current_password"]
    ada.refresh_from_db()
    assert ada.email == "Ada@example.com"
    assert mailoutbox == []


@pytest.mark.parametrize("taken", ["babbage@example.com", "BABBAGE@Example.com"])
def test_email_change_rejects_email_used_by_another_account(
    client, ada, mailoutbox, taken
):
    get_user_model().objects.create_user(
        username="babbage", email="babbage@example.com", password="x"
    )
    client.force_login(ada)

    response = change_email(client, taken, "analytical-engine-1843")

    assert response.context["form"].errors["email"] == [
        "An account with that email already exists."
    ]
    ada.refresh_from_db()
    assert ada.email == "Ada@example.com"
    assert mailoutbox == []


def test_email_change_rejects_current_email(client, ada, mailoutbox):
    client.force_login(ada)

    response = change_email(client, "ada@EXAMPLE.com", "analytical-engine-1843")

    assert response.context["form"].errors["email"]
    assert mailoutbox == []


def test_email_change_saves_and_alerts_old_address(client, ada, mailoutbox):
    client.force_login(ada)

    response = change_email(client, "Lovelace@EXAMPLE.com", "analytical-engine-1843")

    assert response.redirect_chain[-1][0] == reverse("accounts:account")
    assert "Your email is now Lovelace@example.com." in response.content.decode()
    ada.refresh_from_db()
    assert ada.email == "Lovelace@example.com"

    assert len(mailoutbox) == 1
    alert = mailoutbox[0]
    assert alert.to == ["Ada@example.com"]
    assert "changed" in alert.subject
    assert "Lovelace@example.com" in alert.body


def test_adding_email_to_blank_account_sends_no_alert(client, customer, mailoutbox):
    client.force_login(customer)

    response = change_email(client, "casey@example.com", "customer123")

    assert response.redirect_chain[-1][0] == reverse("accounts:account")
    customer.refresh_from_db()
    assert customer.email == "casey@example.com"
    assert mailoutbox == []


# --- Change password -----------------------------------------------------------


def change_password(client, old, new1, new2=None):
    return client.post(
        reverse("accounts:password_change"),
        {
            "old_password": old,
            "new_password1": new1,
            "new_password2": new1 if new2 is None else new2,
        },
        follow=True,
    )


def test_account_page_links_to_password_change(client, ada):
    client.force_login(ada)

    page = client.get(reverse("accounts:account")).content.decode()

    assert reverse("accounts:password_change") in page


def test_password_change_page_renders_in_site_style(client, ada):
    client.force_login(ada)

    response = client.get(reverse("accounts:password_change"))

    assert response.status_code == HTTPStatus.OK
    assert "accounts/password_change.html" in [t.name for t in response.templates]
    assert "base.html" in [t.name for t in response.templates]
    assert 'class="input w-full"' in response.content.decode()


@pytest.mark.parametrize(
    ("old", "new1", "new2", "field"),
    [
        ("difference-engine", "lovelace-notes-g", None, "old_password"),
        (
            "analytical-engine-1843",
            "lovelace-notes-g",
            "lovelace-notes-h",
            "new_password2",
        ),
        ("analytical-engine-1843", "short", None, "new_password2"),
        ("analytical-engine-1843", "12345678901", None, "new_password2"),
        ("analytical-engine-1843", "password", None, "new_password2"),
        ("analytical-engine-1843", "ada@example", None, "new_password2"),
    ],
    ids=["wrong-current", "mismatch", "too-short", "numeric", "common", "similar"],
)
def test_password_change_rejections(client, ada, mailoutbox, old, new1, new2, field):
    client.force_login(ada)

    response = change_password(client, old, new1, new2)

    assert response.context["form"].errors[field]
    ada.refresh_from_db()
    assert ada.check_password("analytical-engine-1843")
    assert mailoutbox == []


def test_password_change_swaps_the_password(client, ada):
    client.force_login(ada)

    response = change_password(client, "analytical-engine-1843", "lovelace-notes-g")

    assert response.redirect_chain[-1][0] == reverse("accounts:account")
    assert "Your password was changed." in response.content.decode()
    client.logout()
    assert sign_in(client, "ada", "analytical-engine-1843").status_code == HTTPStatus.OK
    assert sign_in(client, "ada", "lovelace-notes-g").status_code == HTTPStatus.FOUND


def test_password_change_keeps_this_session_and_ends_others(client, ada):
    other = Client()
    other.force_login(ada)
    client.force_login(ada)

    change_password(client, "analytical-engine-1843", "lovelace-notes-g")

    here = client.get(reverse("accounts:account"))
    there = other.get(reverse("accounts:account"))
    assert here.status_code == HTTPStatus.OK
    assert there.status_code == HTTPStatus.FOUND
    assert there.url.startswith(reverse("accounts:login"))


def test_password_change_alerts_the_account_email(client, ada, mailoutbox):
    client.force_login(ada)

    change_password(client, "analytical-engine-1843", "lovelace-notes-g")

    assert len(mailoutbox) == 1
    alert = mailoutbox[0]
    assert alert.to == ["Ada@example.com"]
    assert "password was changed" in alert.subject


def test_password_change_without_email_sends_no_alert(client, customer, mailoutbox):
    client.force_login(customer)

    response = change_password(client, "customer123", "lovelace-notes-g")

    assert response.redirect_chain[-1][0] == reverse("accounts:account")
    assert mailoutbox == []


# --- Password reset --------------------------------------------------------------


def request_reset(client, email):
    return client.post(reverse("accounts:password_reset"), {"email": email})


def reset_link(message):
    """The confirm URL path from a reset email."""
    match = re.search(r"https?://[^/\s]+(/\S+)", message.body)
    return match.group(1)


def test_login_page_links_to_password_reset(client, db):
    page = client.get(reverse("accounts:login")).content.decode()

    assert "Forgot your password?" in page
    assert reverse("accounts:password_reset") in page


def test_password_reset_page_renders_in_site_style(client, db):
    response = client.get(reverse("accounts:password_reset"))

    assert response.status_code == HTTPStatus.OK
    assert "base.html" in [t.name for t in response.templates]
    assert 'class="input w-full"' in response.content.decode()


@pytest.mark.parametrize("email", ["Ada@example.com", "ADA@EXAMPLE.COM"])
def test_password_reset_emails_a_link_to_the_set_password_form(
    client, ada, mailoutbox, email
):
    response = request_reset(client, email)

    assert response.status_code == HTTPStatus.FOUND
    assert response.url == reverse("accounts:password_reset_done")
    assert len(mailoutbox) == 1
    message = mailoutbox[0]
    assert message.to == ["Ada@example.com"]
    assert message.subject == "Reset your ThoughtTronix password"

    form_page = client.get(reset_link(message), follow=True)
    assert form_page.context["validlink"]
    assert "new_password1" in form_page.context["form"].fields


def test_reset_link_printed_to_the_console_opens_the_form(client, ada, mailoutbox):
    # The link is longer than 78 characters, which makes the raw MIME body
    # quoted-printable; the dev console backend must print it whole.
    request_reset(client, "ada@example.com")
    stream = io.StringIO()
    ReadableConsoleEmailBackend(stream=stream).send_messages(mailoutbox)

    link = re.search(r"https?://[^/\s]+(/\S+)", stream.getvalue()).group(1)

    assert client.get(link, follow=True).context["validlink"]
    assert "=E2=80=94" not in stream.getvalue()


def test_password_reset_for_unknown_email_looks_the_same(client, ada, mailoutbox):
    known = request_reset(client, "ada@example.com")
    mailoutbox.clear()

    unknown = request_reset(client, "nobody@example.com")

    assert mailoutbox == []
    assert unknown.status_code == known.status_code
    assert unknown.url == known.url
    page = client.get(unknown.url).content.decode()
    assert "Check your inbox" in page


def set_new_password(client, link, password):
    """Open a reset link and submit a new password through it."""
    form_page = client.get(link, follow=True)
    return client.post(
        form_page.redirect_chain[-1][0] if form_page.redirect_chain else link,
        {"new_password1": password, "new_password2": password},
        follow=True,
    )


def test_password_reset_link_sets_a_password_the_user_can_sign_in_with(
    client, ada, mailoutbox
):
    request_reset(client, "ada@example.com")

    response = set_new_password(client, reset_link(mailoutbox[0]), "lovelace-notes-g")

    assert response.redirect_chain[-1][0] == reverse("accounts:password_reset_complete")
    assert "Your password has been reset" in response.content.decode()
    assert sign_in(client, "ada", "analytical-engine-1843").status_code == HTTPStatus.OK
    assert sign_in(client, "ada", "lovelace-notes-g").status_code == HTTPStatus.FOUND


def assert_invalid_link_page(response):
    page = response.content.decode()
    assert not response.context["validlink"]
    assert "This link is no longer valid" in page
    assert reverse("accounts:password_reset") in page


def test_used_password_reset_link_is_rejected(client, ada, mailoutbox):
    request_reset(client, "ada@example.com")
    link = reset_link(mailoutbox[0])
    set_new_password(client, link, "lovelace-notes-g")

    response = Client().get(link, follow=True)

    assert_invalid_link_page(response)


def test_password_reset_link_expires_after_one_hour(
    client, ada, mailoutbox, monkeypatch
):
    request_reset(client, "ada@example.com")
    link = reset_link(mailoutbox[0])
    issued = datetime.now()

    monkeypatch.setattr(
        PasswordResetTokenGenerator,
        "_now",
        lambda self: issued + timedelta(minutes=59),
    )
    assert client.get(link, follow=True).context["validlink"]

    monkeypatch.setattr(
        PasswordResetTokenGenerator,
        "_now",
        lambda self: issued + timedelta(hours=1, seconds=5),
    )
    assert_invalid_link_page(Client().get(link, follow=True))


def test_blank_email_user_cannot_be_reset(client, customer, mailoutbox):
    response = request_reset(client, "")

    assert response.status_code == HTTPStatus.OK
    assert response.context["form"].errors["email"]
    assert mailoutbox == []


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


def test_navbar_shows_account_next_to_addresses(client, customer):
    client.force_login(customer)

    page = client.get(reverse("products:catalog")).content.decode()

    addresses = page.index(f'href="{reverse("accounts:address_list")}"')
    account = page.index(f'href="{reverse("accounts:account")}"')
    assert 0 < account - addresses < 200


def test_navbar_hides_account_from_visitors(client, db):
    page = client.get(reverse("products:catalog")).content.decode()

    assert f'href="{reverse("accounts:account")}"' not in page
