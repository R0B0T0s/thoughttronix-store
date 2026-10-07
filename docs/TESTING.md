# Testing

Read this before writing or changing tests.

- pytest + pytest-django; run with `uv run pytest`.
- Test files are named `tests.py` or `test_*.py` inside each app.
- Shared fixtures live in the project-level `conftest.py` — plain fixtures,
  no factory-boy. Available: `customer`, `staff_user`, `category`, `product`,
  `unavailable_product`, `tag`, `cart`, `cart_item`, `coupon`, `address`.
- An autouse `media_root` fixture points `MEDIA_ROOT` at a temp folder, so
  image tests never touch the real `media/`.
- An autouse `clear_cache` fixture empties Django's cache before and after
  each test, so cache-backed state (the password-reset cooldown) never leaks
  between tests.
- The suite must be green at every phase boundary.
