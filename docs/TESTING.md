# Testing

Read this before writing or changing tests.

- pytest + pytest-django; run with `uv run pytest`.
- Test files are named `tests.py` or `test_*.py` inside each app.
- Shared fixtures live in the project-level `conftest.py` — plain fixtures,
  no factory-boy. Available: `customer`, `staff_user`, `category`, `product`,
  `unavailable_product`, `tag`, `cart`, `cart_item`, `coupon`, `address`.
- The suite must be green at every phase boundary.
