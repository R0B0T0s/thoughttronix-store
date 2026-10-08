# Architecture

Read this before adding or changing models, views, forms, services, URLs, or
settings.

## Where logic lives

Logic lives in models and managers; cross-model workflows get a service
module; views stay thin.

Idiomatic Django throughout: class-based views, model methods, custom
managers/querysets, forms own their validation.

## Deep modules

Exactly two deliberate deep modules, with docstrings and type hints on every
public function — their interfaces are the product:

- `orders/services.py` — `place_order`
- `dashboard/queries.py` — the dashboard's aggregations

## URLs

- Every URL is named; every app has a namespace (`products:catalog`,
  `orders:checkout`).
- Public catalog URLs use slugs (`/products/seraphine-home-hub/`);
  back-office URLs use pks.
- `Product` defines `get_absolute_url`.

## Settings

Settings read from `.env` via environs with working defaults — the app must
run with no `.env` present.

With no `.env`, `DEBUG` is on and `SECRET_KEY` is the development default.
Setting `DEBUG=False` without a real `SECRET_KEY` raises
`ImproperlyConfigured` at startup. Debug-off also turns on secure session and
CSRF cookies, `SECURE_SSL_REDIRECT`, and HSTS (`SECURE_HSTS_SECONDS`, default
one year, with subdomains and preload), so `manage.py check --deploy` is
clean. Hardening settings key off `DEBUG`; don't toggle them individually.

The Django admin is mounted at `ADMIN_URL` (default `control-room/`), never
`admin/`. Link to it with `reverse("admin:index")`, never a hard-coded path.

Login lockout is django-axes (the `AXES_*` settings). Its backend must stay
first in `AUTHENTICATION_BACKENDS`, ahead of `accounts.backends`, and its
middleware last in `MIDDLEWARE`.

Email prints to the terminal (`config.mail.ReadableConsoleEmailBackend`)
until `EMAIL_HOST` is set in `.env`; then the SMTP backend is used, with
`EMAIL_PORT`, `EMAIL_HOST_USER`, `EMAIL_HOST_PASSWORD`, and `EMAIL_USE_TLS`
also read from `.env`. All mail is sent from `DEFAULT_FROM_EMAIL` (send with
`from_email=None`). Mail credentials never go in source.
