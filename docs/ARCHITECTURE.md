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
