"""Settings that depend on the environment.

Settings are read once, at import, so each test loads them fresh in a
subprocess with its own environment. The subprocess ignores .env, so a
developer's own mail settings can't change the outcome.
"""

import json
import os
import subprocess
import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

MAIL_KEYS = [
    "EMAIL_HOST",
    "EMAIL_PORT",
    "EMAIL_HOST_USER",
    "EMAIL_HOST_PASSWORD",
    "EMAIL_USE_TLS",
    "DEFAULT_FROM_EMAIL",
]

# Printed as JSON by the subprocess; settings it doesn't define come out null.
# The probe skips reading .env, so only the environment given here counts.
PROBE = """
import json
from environs import env
env.read_env = lambda *args, **kwargs: None
from config import settings
names = [
    "EMAIL_BACKEND", "EMAIL_HOST", "EMAIL_PORT", "EMAIL_HOST_USER",
    "EMAIL_HOST_PASSWORD", "EMAIL_USE_TLS", "DEFAULT_FROM_EMAIL",
]
print(json.dumps({name: getattr(settings, name, None) for name in names}))
"""


def load_settings(**mail_env):
    """The mail settings as loaded with exactly these mail keys set."""
    env = {k: v for k, v in os.environ.items() if k not in MAIL_KEYS}
    env.update(mail_env)
    result = subprocess.run(
        [sys.executable, "-c", PROBE],
        cwd=BASE_DIR,
        env=env,
        capture_output=True,
        text=True,
        check=True,
    )
    return json.loads(result.stdout)


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
