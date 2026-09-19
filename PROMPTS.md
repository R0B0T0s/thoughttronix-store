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
