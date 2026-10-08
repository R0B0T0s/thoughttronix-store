# CLAUDE.md — The ThoughtTronix Store

A server-rendered Django 6 storefront and back office. The PRD (`prd/core-platform.md`) and the plan (`plans/core-platform.md`) record how the core platform was designed and built.

## Commands

- `uv sync` — install dependencies (Python 3.13, managed by uv)
- `uv run python manage.py migrate` — apply migrations
- `uv run python manage.py seed` — reset the database to the demo world
  (destructive, idempotent)
- `uv run python manage.py tailwind runserver` — dev server + Tailwind watch
- `uv run python manage.py tailwind build` — compile production CSS
- `uv run pytest` — run the test suite
- `uv run ruff check .` and `uv run ruff format .` — lint and format

## Project layout

- `config/` — the project package (settings, root urls)
- `accounts/` — custom user model (`accounts.User`, `AbstractUser` + nullable
  `job_title`) and the customer address book (`Address`)
- `products/` — catalog (`Category`, `Product`, `Tag`), its back-office CRUD,
  and the `seed` command
- `coupons/` — discount codes (`Coupon`) and their back-office CRUD
- `orders/` — cart, checkout, orders, and back-office order management
- `dashboard/` — the staff analytics dashboard
- `templates/` — project-level templates (`base.html`); app templates live in
  `templates/<app>/`
- `assets/` — static sources; `assets/css/source.css` is the Tailwind input

## Always

- Roles are Django's own vocabulary: customers are plain users, employees are
  `is_staff`, the admin is `is_superuser`. No role field, no Groups.
- Logic lives in models and managers; cross-model workflows get a service
  module; views stay thin.
- `PROMPTS.md` is the AI-usage log — append entries, never rewrite history.
- `assets/css/tailwind.css` is compiled output (gitignored) — never edit it.
- The Django admin lives at `/control-room/` (`ADMIN_URL` in `.env`), not
  `/admin/`. `DEBUG=False` requires a real `SECRET_KEY` in `.env`; keys are
  documented in `.env.example`.

## Reference docs — read before working in that area

- `docs/ARCHITECTURE.md` — models, views, forms, services, URLs, settings
- `docs/TEMPLATES.md` — read before creating or editing templates
- `docs/TESTING.md` — writing or changing tests
