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

Login lockout is django-axes (the `AXES_*` settings). Its backend must stay
first in `AUTHENTICATION_BACKENDS`, ahead of `accounts.backends`, and its
middleware last in `MIDDLEWARE`.

Email prints to the terminal (`config.mail.ReadableConsoleEmailBackend`)
until `EMAIL_HOST` is set in `.env`; then the SMTP backend is used, with
`EMAIL_PORT`, `EMAIL_HOST_USER`, `EMAIL_HOST_PASSWORD`, and `EMAIL_USE_TLS`
also read from `.env`. All mail is sent from `DEFAULT_FROM_EMAIL` (send with
`from_email=None`). Mail credentials never go in source.
