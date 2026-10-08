"""Settings that depend on the environment.

Settings are read once, at import, so each test loads them fresh in a
subprocess with its own environment. The subprocess ignores .env, so a
developer's own settings can't change the outcome.
"""

import json
import os
import subprocess
import sys
from pathlib import Path

import pytest
from django.urls import reverse

BASE_DIR = Path(__file__).resolve().parent.parent

ENV_KEYS = [
    "SECRET_KEY",
    "DEBUG",
    "ALLOWED_HOSTS",
    "ADMIN_URL",
    "SECURE_HSTS_SECONDS",
    "EMAIL_HOST",
    "EMAIL_PORT",
    "EMAIL_HOST_USER",
    "EMAIL_HOST_PASSWORD",
    "EMAIL_USE_TLS",
    "DEFAULT_FROM_EMAIL",
]

# Long and random enough for Django's own SECRET_KEY check.
STRONG_KEY = "x7#kq9!vL2@pZr$8mWn4^tY6&bH3*jF5(cD1)eG0-sA_uQ+iO=wX;lK:vB<nM>"

PRODUCTION = {"DEBUG": "false", "SECRET_KEY": STRONG_KEY}

# Every probe skips reading .env, so only the environment given here counts.
SKIP_DOTENV = """
from environs import env
env.read_env = lambda *args, **kwargs: None
"""

# Printed as JSON by the subprocess; settings it doesn't define come out null.
PROBE = (
    SKIP_DOTENV
    + """
import json
from config import settings
names = [
    "SECRET_KEY", "DEBUG", "ADMIN_URL",
    "SESSION_COOKIE_SECURE", "CSRF_COOKIE_SECURE", "SECURE_SSL_REDIRECT",
    "SECURE_HSTS_SECONDS", "SECURE_HSTS_INCLUDE_SUBDOMAINS", "SECURE_HSTS_PRELOAD",
    "EMAIL_BACKEND", "EMAIL_HOST", "EMAIL_PORT", "EMAIL_HOST_USER",
    "EMAIL_HOST_PASSWORD", "EMAIL_USE_TLS", "DEFAULT_FROM_EMAIL",
]
print(json.dumps({name: getattr(settings, name, None) for name in names}))
"""
)

DEPLOY_CHECK = (
    SKIP_DOTENV
    + """
from django.core.management import execute_from_command_line
execute_from_command_line(["manage.py", "check", "--deploy", "--fail-level", "WARNING"])
"""
)


def run_python(code, **chosen_env):
    """Run ``code`` with exactly these environment-dependent keys set."""
    env = {k: v for k, v in os.environ.items() if k not in ENV_KEYS}
    env["DJANGO_SETTINGS_MODULE"] = "config.settings"
    env.update(chosen_env)
    return subprocess.run(
        [sys.executable, "-c", code],
        cwd=BASE_DIR,
        env=env,
        capture_output=True,
        text=True,
    )


def load_settings(**chosen_env):
    """The settings as loaded with exactly these keys set."""
    result = run_python(PROBE, **chosen_env)
    assert result.returncode == 0, result.stderr
    return json.loads(result.stdout)


# --- Local defaults and production hardening ---------------------------------


def test_without_env_the_site_runs_in_debug_with_the_dev_key():
    loaded = load_settings()

    assert loaded["DEBUG"] is True
    assert loaded["SECRET_KEY"].startswith("django-insecure-")


def test_debug_leaves_cookies_and_redirects_relaxed_for_local_http():
    loaded = load_settings()

    assert loaded["SESSION_COOKIE_SECURE"] is False
    assert loaded["CSRF_COOKIE_SECURE"] is False
    assert loaded["SECURE_SSL_REDIRECT"] is False
    assert loaded["SECURE_HSTS_SECONDS"] == 0


def test_debug_off_with_the_dev_key_refuses_to_load():
    result = run_python(PROBE, DEBUG="false")

    assert result.returncode != 0
    assert "ImproperlyConfigured" in result.stderr
    assert "SECRET_KEY is still the development default" in result.stderr


def test_debug_off_with_a_proper_key_turns_on_https_hardening():
    loaded = load_settings(**PRODUCTION)

    assert loaded["DEBUG"] is False
    assert loaded["SESSION_COOKIE_SECURE"] is True
    assert loaded["CSRF_COOKIE_SECURE"] is True
    assert loaded["SECURE_SSL_REDIRECT"] is True
    assert loaded["SECURE_HSTS_SECONDS"] == 31536000
    assert loaded["SECURE_HSTS_INCLUDE_SUBDOMAINS"] is True
    assert loaded["SECURE_HSTS_PRELOAD"] is True


def test_hsts_lifetime_comes_from_env():
    loaded = load_settings(**PRODUCTION, SECURE_HSTS_SECONDS="3600")

    assert loaded["SECURE_HSTS_SECONDS"] == 3600


def test_deploy_check_passes_with_no_warnings():
    result = run_python(DEPLOY_CHECK, **PRODUCTION)

    assert result.returncode == 0, result.stderr
    assert "no issues" in result.stdout


# --- Admin URL ----------------------------------------------------------------


def test_admin_url_defaults_to_something_other_than_admin():
    loaded = load_settings()

    assert loaded["ADMIN_URL"] != "admin/"


@pytest.mark.parametrize("given", ["back-room", "/back-room/", "back-room/"])
def test_admin_url_comes_from_env_with_one_trailing_slash(given):
    loaded = load_settings(ADMIN_URL=given)

    assert loaded["ADMIN_URL"] == "back-room/"


@pytest.mark.django_db
def test_admin_is_not_at_slash_admin(client):
    assert client.get("/admin/").status_code == 404


@pytest.mark.django_db
def test_admin_is_reachable_at_the_configured_path(admin_client, settings):
    url = reverse("admin:index")

    assert url == f"/{settings.ADMIN_URL}"
    assert admin_client.get(url).status_code == 200


# --- Email delivery -----------------------------------------------------------


def test_without_mail_settings_emails_print_to_the_terminal():
    loaded = load_settings()

    assert loaded["EMAIL_BACKEND"] == "config.mail.ReadableConsoleEmailBackend"


def test_email_host_switches_to_smtp_with_values_from_env():
    loaded = load_settings(
        EMAIL_HOST="smtp.example.com",
        EMAIL_PORT="2525",
        EMAIL_HOST_USER="store@example.com",
        EMAIL_HOST_PASSWORD="s3cret-from-env",
        EMAIL_USE_TLS="false",
    )

    assert loaded["EMAIL_BACKEND"] == "django.core.mail.backends.smtp.EmailBackend"
    assert loaded["EMAIL_HOST"] == "smtp.example.com"
    assert loaded["EMAIL_PORT"] == 2525
    assert loaded["EMAIL_HOST_USER"] == "store@example.com"
    assert loaded["EMAIL_HOST_PASSWORD"] == "s3cret-from-env"
    assert loaded["EMAIL_USE_TLS"] is False


def test_smtp_defaults_to_port_587_with_tls():
    loaded = load_settings(EMAIL_HOST="smtp.example.com")

    assert loaded["EMAIL_PORT"] == 587
    assert loaded["EMAIL_USE_TLS"] is True


def test_default_from_email_has_a_store_default():
    loaded = load_settings()

    assert "ThoughtTronix" in loaded["DEFAULT_FROM_EMAIL"]


def test_default_from_email_comes_from_env():
    loaded = load_settings(DEFAULT_FROM_EMAIL="Store <hello@example.com>")

    assert loaded["DEFAULT_FROM_EMAIL"] == "Store <hello@example.com>"
