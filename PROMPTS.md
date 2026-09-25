# PROMPTS.md — AI Usage Log

This file is the record of AI use on this codebase. At the end of every
agent session, direct the agent to write the session log with this prompt:

> Append a session log to PROMPTS.md at the repo root, under today's date,
> newest entry at the top. Record every prompt I gave you this session, in
> order, including any corrections. End the entry with a short summary:
> the outcome, any places where I deviated from a recommended answer or
> asked follow-up questions, and anything that went sideways.

Two rules:

- Entries are added only by that prompt, never unprompted.
- New entries go at the top. Never rewrite or delete an old entry — the
  log is part of your work, and an honest log of a session that went
  sideways is worth more than a tidy one.

Each entry has this shape:

    ## YYYY-MM-DD — <one-line summary>

    ### Prompts
    1. ...

    ### Summary
    - **Outcome:** what was built and what was kept
    - **Deviations:** recommendations overridden, follow-up questions asked
    - **Sideways:** failures, wrong turns, and how they were caught

## 2026-09-24 — Add a coupon/discount system, grilled and built end-to-end

### Prompts
1. `/grill-me` — Create a coupon/discount feature that allows customers to type a code at checkout. Allow codes to be created through staff and admin accounts. If a customer tries to use an expired code, return an appropriate message. When a code is created, allow the code to work during a certain stretch of time set by the creator. Retiring a code will not affect any order that has already used it. Do not produce a server error, a blank page, or an opportunity for the customer to contact Legal. The coupon system must support both order-wide discounts and discounts limited to specific products, such as 50% off Seraphine for a limited time.
2. (Interactive `/grill-me` interview: thirteen design questions answered one at a time, covering app placement, discount types, scope modeling, fixed-discount-vs-quantity semantics, no-match handling, checkout entry point, order-level snapshotting, retirement mechanics, usage limits, code casing, over-discount flooring, validation layering, and delete-vs-retire — see Deviations below for the two answers that overrode my recommendation.)
3. Start Implementing
4. How do I manually verify in the browser?
5. One problem I have, Whenever you select a product, it is hard to accurately select which product is desired to have the coupon applied to. Text is overlapping and the areas you click on to select products can be a bit finicky. Please change how products are selected for coupons.
6. Write a session log with the standard prompt in PROMPTS.md

### Summary
- **Outcome:** Built a new `coupons` app: a `Coupon` model (percent or fixed discount, order-wide or product-scoped via an M2M, an active-window pair plus an independent `is_active` retire switch, `check_redeemable`/`discount_for` methods that only ever return messages, never raise) and back-office CRUD (list/create/edit + retire-reactivate, no hard delete) under a new "Coupons" tab. `Order` gained `coupon` (FK, `SET_NULL`), `coupon_code`, and `discount_amount`, denormalized so retiring or deleting a coupon can't change past orders. `place_order`'s formerly-dormant `coupon_code` seam is now live. `CheckoutForm` gained an optional `coupon_code` field with a `clean_coupon_code` that validates against the live cart/user, so a bad code redisplays the full checkout page with a specific field error instead of any kind of crash. Checkout, confirmation, and both order-detail templates show the discount breakdown when one applied. Seed data now includes two demo coupons (`WELCOME10`, `SERAPHINE50`). Added 30 new tests; full suite (229 tests) green, ruff clean. Verified the real flow end-to-end via Django's test client (successful redemption, reuse rejection, unknown code, product-not-in-cart) and by starting the dev server. Later reworked the back-office product picker from a native `<select multiple>` (DaisyUI's styling overlapped its option text, and precise ctrl/cmd-click selection was reported as "finicky") to a scrollable list of full-width, single-click checkboxes, each labeled with its category for disambiguation.
- **Deviations:** Two of the thirteen grill-me questions were answered against my recommendation: coupon codes require an exact case match rather than being normalized to uppercase, and coupons carry a fixed one-redemption-per-customer rule rather than no usage limit at all (both implemented as asked, no pushback needed).
- **Sideways:** A background "Explore" subagent sent to survey the checkout/product/order code before the interview never delivered its report; abandoned it and read the relevant files directly instead, no context lost. One post-implementation test failure (`test_percent_discount_over_100_is_rejected`) came from Django auto-escaping the apostrophe in "can't exceed 100" to `&#x27;t` in rendered HTML, breaking a substring assertion — fixed by rewording the message to "cannot exceed 100" rather than working around the escaping. During a shell smoke test, the em dash in the new "Product — Category" checkbox labels printed as a `�` in the Windows console; raw-byte inspection of the actual HTTP response confirmed correct UTF-8 (`\xe2\x80\x94`) — a terminal display limitation, not a real bug.

## 2026-09-19 — Add `is_featured` to Product, migrate, and surface a Featured badge

### Prompts
1. Add is_featured as a boolean field. DO NOT ADD the badge to anything, only implement it's creation.
2. Generate and apply a migration for the is_featured changes made.
3. Add a "Featured" badge to products. This should correlate to whether a product is featured or not. The "Featured" badge should be located in 2 places at the same time: The catalog listing and the product's detail page.
4. Append a session log to PROMPTS.md at the repo root, under today's date, newest entry at the top. Record every prompt I gave you this session, in order, including any corrections. End the entry with a short summary: the outcome, any places where I deviated from a recommended answer or asked follow-up questions, and anything that went sideways.

### Summary
- **Outcome:** Added `Product.is_featured` (`BooleanField`, default `False`), wired it into `ProductForm` and `ProductAdmin` (list_display/list_filter) so back-office staff can set it, generated and applied migration `0003_product_is_featured`, then added a `badge-accent` "Featured" badge to both `templates/products/catalog.html` (product card) and `templates/products/detail.html` (next to the availability badge), rendering only when `product.is_featured` is true. Full pytest suite (164 tests) stayed green after every step; badge rendering was also spot-checked via Django's test client on both pages.
- **Deviations:** None — each prompt was implemented as a distinct, sequential step (field first with badge explicitly withheld, then migration, then badge) rather than combined ahead of time.
- **Sideways:** None. One minor hiccup during manual verification (an `ALLOWED_HOSTS`/wrong-URL error when smoke-testing via the shell) was self-inflicted tooling friction, not a code defect, and was resolved by fixing the test script.
