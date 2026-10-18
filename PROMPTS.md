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

## 2026-10-18 — Product reviews Phase 6: seed the demo reviews (feature complete)

### Prompts
1. `/implement @prd/reviews.md @plans/reviews.md implement phase 6`
2. Go ahead (no TDD candidates, since the phase is seed data; approve the seed plan)
3. It passes (manual verification passed)

### Summary
- **Outcome:** `seed` now wipes reviews and builds 17 demo reviews from a new `DEMO_REVIEWS` list: 11 reviewers across 9 products, every rating from 1 to 5, 5 reviews with no comment, exactly one "Edited by staff" (Tobi O. on Veil), and one author-edited "(edited)" review (Beverly C. on MindSync). Each review is looked up against `OrderItem.objects.purchased_by` and dated a few days after the earliest qualifying order. A review with no non-cancelled purchase behind it stops the seed with a `CommandError`. Both timestamps are set with a queryset `update()`, because `updated_at` is `auto_now` and a backdated save would otherwise mark every review "(edited)". `customer` has reviewed MindSync and has SyncRest, DreamWeaver, and others still to review. The seed summary reports the review count, and the README logins table mentions the review. Added 4 seed tests to `reviews/tests.py` (spread and markers, every review backed by an earlier purchase, `customer`'s one review plus a reviewable product, and reseeding being identical). The full suite passed (467), Ruff is clean, two consecutive seeds gave the same 17 reviews, and the user verified the phase manually in the browser.
- **Deviations:** None. The plan was approved as proposed.
- **Sideways:** The background orders are random (seeded), so I first ran the seed and listed each product's non-cancelled purchasers, then wrote the background reviews against that list. If the order generator changes, the seed fails loudly instead of writing an unbacked review. My first purchaser query, piped into `manage.py shell` over stdin, failed with a syntax error from the interactive console, and I re-ran it with `shell -c`. `pytest -n auto` isn't available (no xdist), so the suite ran serially. The untracked `.claude/skills/` folders were left alone.

## 2026-10-18 — Product reviews Phase 5: staff moderation edit

### Prompts
1. `/implement @prd/reviews.md @plans/reviews.md implement phase 5`
2. approved (the three TDD behaviors: `staff_edit` changes only the comment and sets the flag; a staff save of another user's review ignores the posted rating and shows "Edited by staff"; staff editing their own review get the full author form and saving clears the flag)
3. Yes (approve the `staff_edit` test and make it pass)
4. Yes (move on to behavior 2)
5. Approved (the staff-save test)
6. Yes (move on to behavior 3)
7. Continue (keep behavior 3's test as a regression guard and do the rest of Phase 5)
8. Everything works (manual verification passed)

### Summary
- **Outcome:** Added `Review.staff_edit(comment)`, which saves only the comment, the staff flag, and the timestamp (`update_fields`), so the rating can't change. Added the comment-only `StaffReviewForm`. `EditReviewView` now allows anyone `can_change` permits. Authors, including staff editing their own review, get the author form and `author_edit`; staff editing someone else's review get the staff form and `staff_edit`. `section_context` now hands the template a separate `edit_form` next to the create `form`. In the list, staff see Edit on every review, and the card being moderated swaps in place to the reviewer's name, read-only stars, a "the customer's rating can't be changed" note, and the comment-only form with Cancel. `_form.html` shows the star radios only when the form has a rating field. Added 7 tests (3 TDD, 4 normal) and removed `test_only_the_author_sees_the_edit_button`, which the new Edit-buttons test replaces; the reviews suite is at 67, the full suite passed (464, run before that removal), and Ruff is clean. The user verified the phase manually in the browser.
- **Deviations:** None. Every proposal was approved as made.
- **Sideways:** Behavior 1's rating assertion already passed against the no-op stub; I said so when showing RED, and behavior 2's test covers a posted rating being ignored. Behavior 3's test was never RED, because behavior 2's form choice already checked authorship first. I said so and ran a temporary mutation (staff always get the staff form) to show the test catches it, then restored `views.py`. While building the templates I found that a staff member who had bought the product would see the staff form in their own empty "Your review" box while moderating, since both forms shared the `form` context variable; I split it into `form` and `edit_form` and added a test. The full-suite run went past the 2-minute foreground timeout and finished in the background. The untracked `.claude/skills/` folders were left alone.

## 2026-10-18 — Product reviews Phase 4: delete a review

### Prompts
1. `/implement @prd/reviews.md @plans/reviews.md implement phase 4`
2. approved, go ahead (the three TDD behaviors: the author deletes and gets the empty form back, another customer gets 403, Delete buttons show only to those allowed and ask first)
3. approved, make it pass (author-delete test)
4. yes, move on to behavior 2
5. approved, make it pass (403 test)
6. yes, move on to behavior 3
7. approved, make it pass (Delete-button test)
8. Go ahead (the rest of Phase 4)
9. manual verification passed

### Summary
- **Outcome:** Three behaviors were built test-first, each shown failing on an assertion and approved before being made to pass. (1) POST `reviews:delete` removes the author's review and returns the section with the empty "Post review" form and the "No reviews yet" summary. (2) Another signed-in customer gets 403 and the review survives; the view reuses `Review.can_change(user)`, so any staff member may delete too. (3) Delete buttons, each with `hx-confirm="Delete this review?"`, render on the pinned "Your review" for its author and on every listed review for staff, and nowhere for other customers. `_review.html` gained an optional `can_delete`; the list passes `user.is_staff`, since the user's own review is always pinned, never listed. Staff deleting any review (summary updates), POST-only (405), anonymous redirect to sign-in, and the 404 were tested normally. The reviews suite went from 54 to 61 tests; the full suite has 457 passing, and Ruff is clean. The user verified the phase manually in the browser.
- **Deviations:** None. Every proposal was approved as made.
- **Sideways:** The first behavior's code briefly let any signed-in user delete any review; I flagged that when it went green, and behavior 2's test closed it. The template's staff check repeats the rule in `can_change` instead of calling it, because templates can't pass an argument; I pointed this out, and the server-side check is the real guard. The full-suite run went past the 2-minute foreground timeout and finished in the background (457 passed in about 2 minutes). `ruff format` reflowed `reviews/urls.py`. The untracked `.claude/skills/` folders were left alone.

## 2026-10-18 — Product reviews Phase 3: author edit and cancel

### Prompts
1. `/implement @prd/reviews.md @plans/reviews.md implement phase 3`
2. I approve (the three TDD behaviors: `author_edit`, saving an edit shows "(edited)" even after the order is cancelled, another customer gets 403)
3. Pass it (`author_edit` test)
4. yes, move on to behavior 2
5. Pass it (edit-save test)
6. Move on
7. Pass it (403 test)
8. Go ahead (the rest of Phase 3)
9. Everything works. Manual review passed

### Summary
- **Outcome:** Three behaviors were built test-first, each shown failing on an assertion and approved before being made to pass. (1) `Review.author_edit(rating, comment)` saves both fields and clears `edited_by_staff`. (2) POST `reviews:edit` validates with `AuthorReviewForm`, applies `author_edit`, and returns the section with the new comment, "(edited)", and an updated summary, even after the author's only order is cancelled. (3) Another signed-in customer gets 403 on GET and POST and the review is unchanged. `Review.can_change(user)` (author or any staff) was added and unit-tested. For now the edit view lets only the author through: staff editing others' reviews waits for Phase 5's comment-only form, so staff can't change a customer's stars through the author form in the meantime. The rest was built and tested normally. `section_context`/`render_section` gained an `editing` argument. GET `reviews:edit` swaps the pinned "Your review" box to a pre-filled form ("Save changes" plus a Cancel button that re-fetches `reviews:section`). Invalid edits re-render that form with errors and input kept, leaving the saved review untouched. The pinned review gained an Edit button, shown only to its author. `_form.html` gained optional `submit_label` and `cancel_url`, and `_review.html` an optional `can_edit`. The reviews suite went from 41 to 54 tests; the full suite has 450 passing, and Ruff is clean. The user verified the phase manually in the browser.
- **Deviations:** None. Every proposal was approved as made.
- **Sideways:** The first RED run of the `author_edit` test was blocked by the auto-mode permission check. Plan mode was then switched on mid-cycle, after the stub and test had been written, so the remaining steps were written up as a plan and approved before the run went ahead. My first 403 check (`can_change(...) and user is the author`) was redundant; it was simplified to the author check after going green, with no change in behavior. The full-suite run went past the 2-minute foreground timeout and finished in the background (450 passed in about 2 minutes). `ruff format` reformatted `reviews/tests.py`. The untracked `.claude/skills/` folders were left alone.

## 2026-10-18 — Product reviews Phase 2: post a review

### Prompts
1. `/implement @prd/reviews.md @plans/reviews.md implement phase 2`
2. Approved (the three TDD behaviors: `can_review`, non-purchasers can't create, a duplicate create keeps one review)
3. Approved (`can_review` test)
4. Approved (continue to the create view)
5. Approved (non-purchaser test)
6. Go ahead (duplicate-create behavior)
7. I do approve (duplicate-create test)
8. Go ahead (the rest of Phase 2)
9. Manual conformation has passed

### Summary
- **Outcome:** Three behaviors were built test-first, each shown failing on an assertion and approved before being made to pass. (1) `Review.can_review(user, product)`: signed in, bought the product (through the Phase 1 `purchased_by` query), and not yet reviewed it. (2) `reviews:create` raises a 403 for a non-purchaser, including one whose only order is cancelled, and saves nothing. (3) A second create from the same user returns the section showing the existing review instead of an error. The view checks for an existing review before the purchase rule, and it also catches the unique constraint's `IntegrityError` inside `transaction.atomic()`, so even simultaneous requests can't produce an error or a duplicate. The rest was built and tested normally. `AuthorReviewForm` (a ModelForm whose rating is a required 1–5 radio choice with the message "Choose a star rating.", and whose comment is optional and limited to 2,000 characters by the model field) was added. So were `reviews/views.py`, with `section_context`/`render_section` shared by the inclusion tag and the views, `ReviewSectionView` (GET, anyone) and the POST-only, sign-in-required `CreateReviewView`, plus `reviews/urls.py` mounted at the root. The "Your review" box now has four states: sign-in link, own review pinned (and left out of the list below), HTMX empty form, and the purchasers-only note. Every response replaces `#reviews` whole. `_stars.html` gained a radio-input mode (via `name=`). Review details moved into a shared `_review.html` partial, and the form lives in `_form.html`. Products are looked up in the full set, so unavailable products can be reviewed. The reviews suite went from 26 to 41 tests; the full suite has 437 passing, and Ruff is clean. The user verified the phase manually in the browser.
- **Deviations:** None. Every proposal was approved as made. The textarea deliberately has no `maxlength` attribute, so an over-long paste reaches the server and shows the length error instead of being silently truncated by the browser.
- **Sideways:** Behavior 3's first run ended in a `PermissionDenied` traceback, which looked at first like a scaffolding error. It was really Django logging the exception behind an assertion failure (`403 == 200`), confirmed before the test was presented as RED. The first full-suite run went past the 2-minute foreground timeout and finished in the background (437 passed in about 2 minutes). Two assertions in the non-TDD tests were tightened before their first run: a vacuous `startswith(...) or ...` check, and a "checked" check that would have matched any star. `docs/ARCHITECTURE.md` doesn't cover the wishlist or reviews, so it wasn't updated. The untracked `.claude/skills/` folders were left alone.

## 2026-10-18 — Product reviews Phase 1: the read-only Reviews section

### Prompts
1. `/implement @prd/reviews.md @plans/reviews.md implement phase 1`
2. Approved (the three TDD behaviors: the purchase query, the rating summary, `was_edited`)
3. Pass it (purchase query test)
4. Move on to the rating summary
5. Pass it (rating summary test)
6. Go for it (`was_edited`)
7. Approved (`was_edited` test, with the one-minute cut-off)
8. Build the rest of Phase 1
9. Manual verification passed

### Summary
- **Outcome:** Three behaviors were built test-first, each shown failing on an assertion and approved before being made to pass. (1) `OrderItem.objects.purchased_by(user, product)` in `orders`: the user's lines for the product on any order that isn't cancelled. (2) `Review.objects.summary()`: the average to one decimal plus the count, computed by one aggregate query, with `None`/`0` for no reviews. (3) `Review.was_edited`: true when the review was updated more than one minute after it was created. The rest was built and tested normally. A new `reviews` app was added to `INSTALLED_APPS`. Its `Review` model has CASCADE FKs to user and product, a unique (user, product) constraint, a 1–5 rating check constraint, newest-first ordering, a `created_at` default that the seed can backdate, and `reviewer_name` (first name + last initial, falling back to the first name alone, then the username). Migration `reviews/0001_initial` was added, and `Review` is registered in the admin. The product detail page renders the section through a `{% reviews_section product %}` inclusion tag, so `products` doesn't depend on `reviews`. The section shows the summary or "No reviews yet — be the first", a "Your review" box (a sign-in link with `next` back to the product, or the purchasers-only note), and every review with name, "Verified purchase" badge, read-only DaisyUI stars from a reusable `_stars.html` partial, comment, date, and "(edited)" / "Edited by staff" markers. New shared fixtures `purchased_product` and `review` were added to `conftest.py` and listed in `docs/TESTING.md`. Added 26 tests. Full suite at 419 passed, Ruff clean, `makemigrations --check` clean. The user verified the phase manually in the browser, with reviews added through the admin.
- **Deviations:** None. Every proposal was approved as made, including the one-minute grace period for "(edited)". In the summary I pointed out that floats round half-to-even (4.25 → 4.2), and in the purchase query that excluding cancelled orders means any future order status counts as a purchase. Both were left as built. A signed-in purchaser sees no "Your review" box in this phase, since the form arrives in Phase 2. I flagged this at manual verification, and it raised no objection.
- **Sideways:** Two new page tests first failed because they expected the apostrophe in "who've" to be escaped as `&#x27;`. Django escapes only variables, not literal template text, so the expected string was corrected (a mechanical fix to the tests, not a change to what they assert). `tailwind build` first reported the stylesheet "up to date" after the new templates were added; a `--force` rebuild confirmed `.rating` and `mask-star-2` are compiled. The earlier uncommitted `PROMPTS.md` entries, the PRD and the plan are included in this commit. The untracked `.claude/skills/` folders were left alone.

## 2026-10-18 — Product reviews: implementation plan (no code yet)

### Prompts
1. `/prd-to-plan @prd/reviews.md`
2. I approve
3. Update PROMPTS.md.

### Summary
- **Outcome:** Read the reviews PRD, the wishlist plan (as the format to follow), the `Order`/`OrderItem` models, the root and product/wishlist URL confs, and the shared `conftest.py` fixtures. Proposed the decisions that apply to every phase: a new `reviews` app mounted at the root; `reviews:section`, `reviews:create`, `reviews:edit` (GET form / POST save) and `reviews:delete`, all keyed by product or review pk; the `Review` model with its constraints; the purchase rule as an `OrderItem` queryset method; and one HTMX swap target for the whole section. Also proposed six phases: (1) the read-only Reviews section with model, admin, and display; (2) posting a review; (3) author edit and cancel; (4) delete; (5) staff moderation edit; (6) seed data and `PROMPTS.md`. The breakdown was approved unchanged and written to `plans/reviews.md`. No application code was changed and nothing was committed.
- **Deviations:** None. I asked three questions (split Phase 1? merge delete with staff edit? product pk rather than slug in URLs?), and the user approved the breakdown as proposed without answering them individually, so the defaults stand: Phase 1 is not split, delete and staff edit remain separate phases, and URLs use pks.
- **Sideways:** Nothing went wrong. Phase 1 is the heaviest slice because it covers everything a shopper sees before any write path exists; that trade-off was flagged in the proposal. The untracked `.claude/skills/implement/` and `.claude/skills/ttd/` folders and the earlier uncommitted `PROMPTS.md` entry were left as they were.

## 2026-10-18 — Product reviews: grill interview and PRD (no code yet)

### Prompts
1. `/grill-me` Create a product review system. Customers should be able to leave only one review per product. Each review is a written comment and a rating. Customers can edit and delete only their reviews. Customers can only leave a review for a product that they have purchased. Staff can edit and delete any review. When creating, editing, or deleting a review should update the website smoothly without needing to reload the page or cause the customer to lose their place.
2. (Interactive `/grill-me` interview: fifteen design questions answered one at a time, covering what counts as purchased (any non-cancelled order), what a later cancellation does (nothing; checked only at creation), rating and comment (1–5 whole stars, comment optional), where ratings show (detail page only), where staff moderate (in place on the product page, plus the Django admin), what the HTMX swap redraws (the whole reviews section), editing layout (pinned "Your review" box, edit in place), delete confirmation (`hx-confirm`), what non-eligible visitors see (a message for each case), staff edit scope (comment only, marked "Edited by staff"), edit markers (an author edit clears the staff marker; author edits show "(edited)"), reviewer name (first name + last initial, falling back to username), pagination (none), seed data (a realistic spread, each review backed by a real order), and where the purchase check lives (an `orders` queryset method, no service module).)
3. `/to-prd`
4. Update prompts.md with a standard prompt

### Summary
- **Outcome:** Before the interview, read `docs/ARCHITECTURE.md`, `docs/TEMPLATES.md`, the wishlist PRD, the `Order`/`OrderItem` models, the product detail view and template, and the back-office shell. That settled several points from the code instead of asking: HTMX is the way to update in place, roles are `is_staff`, purchases can be checked through `OrderItem`, the detail page shows unavailable products, and in-place deletes elsewhere have no confirmation. The interview produced a 15-point design, and `/to-prd` turned it into `prd/reviews.md`. It has 41 user stories, the design decisions, what's out of scope, and a list of what the tests should cover. No application code was changed, nothing was committed, and the PRD is untracked.
- **Deviations:** Question 3 overrode my recommendation of a required comment; the comment is optional. This also departs from the original request ("each review is a written comment and a rating"), and the PRD records it as a deliberate choice. Every other question took the recommended option. No follow-up questions were asked during the interview.
- **Sideways:** The answer to Question 1 was "1" rather than an option letter; I read it as the first option (A, any non-cancelled order) and said so in my next reply. The PRD includes four details the user never voted on, taken from existing project patterns: a double-submit shows the existing review instead of an error, an unauthorized signed-in user gets a 403 while anonymous users are sent to sign in, an invalid form redraws with errors and keeps the input, and staff reviewing their own purchase get the full author form. I flagged all four in my reply so they can be changed. Prompt 4 asked for "a standard prompt"; I took that to mean the standard session-log entry described at the top of this file. The untracked `.claude/skills/implement/` and `.claude/skills/ttd/` folders existed before this session and were left alone.

## 2026-10-18 — Wishlist Phase 5: seed the demo wishlist (feature complete)

### Prompts
1. Implement phase 5 please.
2. Approved (no TDD behaviors for this phase: it's seed data on an already-tested seed pattern, so regular tests instead)
3. Manual verification has passed.

### Summary
- **Outcome:** `seed` now wipes wishlists (`Wishlist.objects.all().delete()`, alongside carts). It then gives the demo `customer` a three-item wishlist from a new `CUSTOMER_WISHLIST` list: SoulSear Mark I (unavailable, so the demo shows the "Unavailable" badge), RecallPro, and Pulse Halo. The items are saved oldest first, so the page lists Pulse Halo at the top. The summary line now ends "…and a live cart and a 3-item wishlist for 'customer'." I updated the command's docstring and the README demo-login table. Two tests in `wishlist/tests.py` cover it: the seeded wishlist has 2–3 items with at least one unavailable, and a second seed rebuilds the identical wishlist, with exactly one wishlist in the database. The full suite passed at 392 and ruff is clean. Running `seed` twice by hand printed the same summary both times. Ticked off Phase 5 in `plans/wishlist.md`, which completes the wishlist plan; the PRD's request for this feature's PROMPTS.md entries is met by the Phase 3, 4, and 5 entries. Manual browser verification passed.
- **Deviations:** None. Following the TDD skill, I proposed no test-first behaviors for a seed-data phase, and the user approved that.
- **Sideways:** The full test run hit the 120-second foreground timeout and finished in the background (392 passed). Running `seed` by hand to check it reset the dev database, which wiped whatever was saved during earlier manual verification. I reported that after it happened rather than asking first, even though `seed` is documented as the destructive reset command. `docs/TEMPLATES.md` still says pages use Times New Roman (see the Phase 3 entry); it hasn't been changed. I didn't open the page in a browser myself; the user did.

## 2026-10-18 — Wishlist Phase 4: remove from the wishlist page

### Prompts
1. implement phase 4
2. approved (the two TDD behaviors: removal returns the list without the item, and another user's wishlist is never touched)
3. approve (test 1)
4. Lets move on (test 1 green; on to test 2)
5. Approve (test 2)
6. Manual verification has passed.

### Summary
- **Outcome:** Added `wishlist:remove_item` at `wishlist/items/<pk>/remove/`. It's POST-only and requires sign-in. It deletes `wishlist.items.filter(product_id=pk)` from the signed-in user's own wishlist and re-renders `wishlist/partials/_list.html`; when the last item goes, that's the empty state. Each row on the wishlist page has a red "Remove" button (`hx-post`, `hx-target="#wishlist-items"`). The products-loaded query moved onto the model as `Wishlist.listing()`, so the page and the endpoint load items the same way; the Phase 3 query-count test still covers it. Two behaviors were built test-first: removal returns the list partial without the item, and naming a product saved only on another user's wishlist leaves their list unchanged. Four more tests cover the sign-in redirect, POST-only, the last removal showing the empty state, and the Remove button markup. That makes 48 wishlist tests; the full suite passed at 390 and ruff is clean. Ticked off Phase 4 in `plans/wishlist.md`. Manual browser verification passed.
- **Deviations:** None overridden. I flagged one choice: an unsaved or stale product pk does nothing and returns the current list rather than a 404, so a double-click still redraws correctly. The plan didn't specify either way, and the user moved on without changing it.
- **Sideways:** The second TDD test (another user's wishlist) passed on its first run, because the one-line fix for test 1 was already limited to the user's own wishlist. It never went red against the real code. To show the test does catch a regression, I briefly swapped in an unscoped `WishlistItem.objects.filter(...).delete()`, watched the test fail on `other_wishlist.contains(product)`, and restored the scoped version. I didn't open the page in a browser myself; the user did.

## 2026-10-17 — Wishlist Phase 3: the wishlist page and navbar link (with Phases 1–2)

### Prompts
1. `/implement` @prd/wishlist.md @plans/wishlist.md implement phase <N>
2. (Asked which phase, since `<N>` was never filled in. Answered "Phase 3 (Recommended)".)
3. approved, go ahead (the three TDD behaviors: own items newest first, the "Unavailable" badge, and no N+1 queries)
4. approved, go ahead (test 1)
5. approved, go ahead (test 1 green; on to test 2)
6. approved, go ahead (test 2)
7. approved (test 2 green; on to test 3)
8. approved (test 3)
9. Continue
10. The wishlist page is using a different font than the rest of the website, please fix this.
11. manual verification passed, congratulations

### Summary
- **Outcome:** Added `wishlist:detail` at `/wishlist/`. It's a `LoginRequiredMixin` `TemplateView` that loads the signed-in user's items with `select_related("product__category")`; the category is needed because the placeholder image comes from it. `templates/wishlist/detail.html` extends `base.html` and wraps `templates/wishlist/partials/_list.html` in `#wishlist-items`, so Phase 4 can swap it. Each row shows the image (through `products/partials/_image.html`), the name linked to the detail page, the price, and an "Unavailable" badge for unavailable products. An empty wishlist shows a 💭 empty state with a "Browse the catalog" button. `base.html` has a plain "Wishlist" link for signed-in users between Addresses and Account. Three behaviors were built test-first, each test approved before code was written and shown failing on an assertion first: own items only, newest first; the badge only on unavailable products; and a query count that doesn't grow with the number of items (6 vs 9 queries before `select_related`). Six more tests cover the sign-in redirect, the row contents, a deleted product dropping off, the empty state, and the navbar link shown and hidden. That makes 42 wishlist tests; the full suite passed at 384 and ruff is clean. Manual browser verification passed. This commit also carries Phases 1–2 (the app, models, migration, add and remove endpoints, the detail-page button, and the `wishlist` fixture), which were already built but uncommitted when the session started.
- **Deviations:** Took the recommended phase when asked. After green, every TDD step was approved without changes.
- **Sideways:** `docs/TEMPLATES.md` says pages use Times New Roman, so I wrapped the wishlist page in `font-['Times_New_Roman',serif]`, copying the recall notices page. In the browser it stood out from every other page, which use the theme font. The user caught it, and I removed the wrapper. That doc line is still misleading and hasn't been changed. Tailwind's normal build reported "up to date" after new classes were added, so I ran a forced rebuild and confirmed `h-20`, `w-24`, and `shrink-0` were compiled. I didn't open the page in a browser myself; the user did.

## 2026-10-07 — Account security Phase 9: production hardening and a configurable admin URL

### Prompts
1. @prd/account-security.md @plans/account-security.md Do Phase 9.
2. I want to verify this in the browser, how would I do that?
3. Update PROMPTS.mv

### Summary
- **Outcome:** In `config/settings.py`, the development key is now a named `DEV_SECRET_KEY`. Loading settings with `DEBUG` off and that key raises `ImproperlyConfigured` with a message saying to set a real `SECRET_KEY`. With debug off, `SESSION_COOKIE_SECURE`, `CSRF_COOKIE_SECURE`, `SECURE_SSL_REDIRECT`, HSTS subdomains, and HSTS preload are all on, and `SECURE_HSTS_SECONDS` is one year (it can be overridden from `.env`). With debug on, all of them stay off, so local work over plain `http://127.0.0.1` is unchanged. `ADMIN_URL` is read from `.env` with a default of `control-room/`, and its slashes are cleaned up to a single trailing one. `config/urls.py` mounts the admin there instead of at `admin/`. `config/tests.py` was generalized: one environment key list, a `run_python` helper that also reports failures, and a shared stub that skips reading `.env`. It gained 12 tests: the debug-on defaults; relaxed settings under debug; the refusal to start with the dev key; every hardening setting with a strong key; the HSTS override; a full `check --deploy --fail-level WARNING` run with no issues; the admin path's default and three spellings from `.env`; `/admin/` returning 404; and the admin opening at the configured path. The suite went from 330 to 342 passing; ruff and `manage.py check` are clean. I also ran `check --deploy` by hand: no issues under the hardened settings, and the expected 6 warnings under the dev defaults. Updated the Settings section of `docs/ARCHITECTURE.md`, `CLAUDE.md`, `.env.example` (the new keys plus a command that generates a key), and the admin path in `README.md`. Ticked off Phase 9 in `plans/account-security.md`, which completes the plan. For prompt 2, I gave a four-part checklist. The admin path and a custom `ADMIN_URL` are checked in the browser. The startup refusal, `check --deploy`, and the HTTPS redirect (`curl.exe -I`) are checked in PowerShell with temporary environment variables, followed by cleanup steps. Nothing committed.
- **Deviations:** I didn't append this entry while building Phase 9, even though the plan asked for one. This file's rule says entries are added only when the user asks, so I left that last plan box unticked until prompt 3. Two choices went beyond the plan, and I flagged both: HSTS subdomains and preload are on, because `check --deploy` warns without them; and the HSTS lifetime can be set from `.env`. I left out `SECURE_PROXY_SSL_HEADER`, because the PRD puts hosting choices out of scope, and noted that a host where a proxy handles HTTPS would need it. No recommendations were overridden.
- **Sideways:** Nothing failed; the suite passed on the first run. For prompt 2, I recommended checking the debug-off redirect with `curl` or a private window rather than a normal browser window. The redirect is a permanent 301, which browsers cache, so it could break local `http://127.0.0.1:8000` until the browser cache was cleared. The secure cookies and the HSTS header can't be seen on the local HTTP dev server, so they're covered only by the tests and the deploy check. With debug on, the 404 page at `/admin/` lists the real admin path; that's expected in debug mode. Whether the browser checks were run hasn't been reported back. I didn't open the pages in a browser myself. Prompt 3's "PROMPTS.mv" was read as PROMPTS.md.

## 2026-10-07 — Account security Phase 8: real email delivery from the environment

### Prompts
1. @prd/account-security.md @plans/account-security.md Do Phase 8.
2. I would like to manually verify in the browser, how would I do that?
3. the mail server does not show anything. The email does not show up in the first terminal.
4. Add to PROMPTS.md

### Summary
- **Outcome:** `config/settings.py` now reads `EMAIL_HOST` from `.env`. When it's blank (the default), `EMAIL_BACKEND` stays `config.mail.ReadableConsoleEmailBackend`. When it's set, the SMTP backend is used, with `EMAIL_PORT` (default 587), `EMAIL_HOST_USER`, `EMAIL_HOST_PASSWORD`, and `EMAIL_USE_TLS` (default on) also read from `.env`. `DEFAULT_FROM_EMAIL` comes from `.env`, defaulting to `The ThoughtTronix Store <no-reply@thoughttronix.example>`. The alert service and the reset view already send with `from_email=None`, so both pick up that address with no code change. `.env.example` lists every mail key, commented out. Added `config/tests.py` with five tests that load settings in a subprocess (settings are read once at import) with a chosen environment and `.env` reading switched off: console by default, SMTP plus every value from the environment once a host is set, the 587/TLS defaults, and the default and overridden "from" address. Added two tests to `accounts/tests.py` checking that the alert and reset emails are sent from `DEFAULT_FROM_EMAIL`. The suite went from 323 to 330 passing; ruff is clean. Added an email paragraph to the Settings section of `docs/ARCHITECTURE.md`, noted the subprocess pattern in `docs/TESTING.md`, and ticked off Phase 8 in `plans/account-security.md`. For prompt 2, I gave a two-part browser checklist: console mode (request a reset and read the email in the runserver terminal), then SMTP mode against a throwaway local server (`uvx aiosmtpd -n -l localhost:1025`, with Mailpit as an alternative) using a `.env` with `EMAIL_USE_TLS=False` and a server restart. Nothing committed.
- **Deviations:** None from the plan. The docs updates were done here rather than waiting for Phase 9, because they were short and describe exactly what this phase added. Prompt 3 was a follow-up when the browser check didn't work.
- **Sideways:** My first version of the settings tests isolated keys by setting them to empty strings. environs treats an empty variable as a real value, so two tests failed (an empty `EMAIL_USE_TLS` can't be parsed as a boolean, and an empty `DEFAULT_FROM_EMAIL` overrode the default). I fixed it by removing the keys from the subprocess environment and stubbing out `env.read_env`, which also keeps a developer's own `.env` from affecting the result. I also dropped a tautological "no credentials in source" test before running. In the browser check (prompt 3), the mail settings had been added uncommented to `.env.example` instead of a new `.env`. The app only reads `.env`, so it stayed on the console backend and the mail server got nothing. I confirmed no `.env` existed and listed the registered users' emails. The empty Django terminal was most likely the earlier phases working as designed: no email is sent for an unregistered address, or within the 5-minute reset cooldown. I gave the fix (create `.env`, restart the server, use a registered address not tried in the last 5 minutes). I recommended removing the uncommented lines from `.env.example` but left the file as the user edited it, so those four live lines are still there at the time of this entry. Whether the SMTP check then worked in the browser hasn't been reported back. I didn't open the pages in a browser myself.

## 2026-10-07 — Account security Phase 7: login lockout with django-axes

### Prompts
1. @prd/account-security.md @plans/account-security.md Do Phase 7.
2. I would like to verify in the browser, how do I do that?
3. how can staff clear a lockout?
4. Update PROMPTS.md

### Summary
- **Outcome:** Added django-axes 8.3.1 (`uv add`) and ran `migrate` on the local database for its tables. In `config/settings.py`: `axes` is in `INSTALLED_APPS`, `AxesStandaloneBackend` comes before `UsernameOrEmailBackend`, and `AxesMiddleware` is last in `MIDDLEWARE`. The `AXES_*` settings lock a username + IP pair after 5 failures for 15 minutes, and a successful sign-in resets the count. A locked-out attempt gets the styled `templates/accounts/locked_out.html` page with a 429 status. It's rendered by a small `locked_out` callable in `accounts/views.py`, shows the wait time, and links to password reset. `accounts/admin.py` swaps axes' `AccessAttemptAdmin` for a subclass that lets any `is_staff` user view and delete lockouts, because employees have no model permissions and the project uses no Groups. An autouse `axes_disabled` fixture in `conftest.py` turns axes off for the ordinary suite, and an `axes_on` fixture turns it back on for the lockout tests. Added seven tests: five failures lock out even the correct password; four don't; mixed username and email spellings share one count; another username from the same IP isn't locked out; the same username from another IP isn't locked out; staff see the lockout in the admin; and when staff clear it with the admin's delete action, the user can sign in again. The suite went from 316 to 323 passing; ruff and `manage.py check` are clean. Added short notes to `docs/TESTING.md` and `docs/ARCHITECTURE.md`, and ticked off Phase 7 in `plans/account-security.md`. For prompt 2, I gave a browser checklist using the seeded `customer`, `employee`, and `admin` accounts, with `axes_reset` to clear stuck lockouts. For prompt 3, I explained clearing a lockout through Admin → Axes → Access attempts (the bulk delete action or the single-record Delete), warned that "Clean up expired attempts" won't unlock an active lockout, and listed the `axes_reset` / `axes_reset_username` commands. Nothing committed.
- **Deviations:** Two decisions went beyond the plan, and I flagged both in my reply. First, an `AXES_USERNAME_CALLABLE` (`accounts.backends.lockout_username`) maps every spelling of an account to its username. Without it, an attacker could dodge the lockout by switching between the username and differently-capitalized emails. This meant pulling the user lookup out into a module-level `find_user` shared by the backend and the callable. Second, the staff-access admin subclass. The plan said "staff can view and clear lockouts", but by default axes' admin is visible only to the superuser. No recommendations were overridden.
- **Sideways:** Nothing failed. The existing 316 tests passed on the first run with axes installed and the fixture in place. A password reset doesn't lift an active lockout, so a customer must wait out the cool-off or ask staff. This is noted on the lockout page rather than changed. `seed` doesn't clear axes records, so lockouts survive a reseed. The admin still lives at `/admin/` until Phase 9. I didn't open the pages in a browser myself; everything was checked through the test client only.

## 2026-10-07 — Account security Phase 6: per-email password-reset cooldown

### Prompts
1. @prd/account-security.md @plans/account-security.md Do Phase 6.
2. I would like to verify the changes with the browser, ho would I do that?
3. Update PROMPTS.md

### Summary
- **Outcome:** `StyledPasswordResetForm` now overrides `save()` so each address gets at most one reset email per `COOLDOWN_SECONDS` (5 minutes). It uses `cache.add`, which only writes when the key is missing, on a key built from a SHA-256 hash of the lowercased address. Different capitalizations therefore share one cooldown, and the cache never holds a raw email. A throttled request still redirects to the same "Check your inbox" page. No `CACHES` setting was added, so the project uses Django's default in-memory cache. Added an autouse `clear_cache` fixture to `conftest.py` and noted it in `docs/TESTING.md`. Added five tests: a second request within the cooldown sends nothing but gets the same response; capitalization is ignored; at 4 minutes the request is still blocked, and at 5 minutes 5 seconds it sends again (via a monkeypatched `time.time`); different addresses have separate cooldowns; and the cache starts empty in each test. Suite at 316 passed, ruff clean. Ticked off Phase 6 in `plans/account-security.md`. For prompt 2, gave a browser checklist using the seeded `customer@example.com` and `employee@example.com`, reading the emails in the runserver terminal. Nothing committed.
- **Deviations:** One decision went beyond the plan: the cooldown also applies to addresses with no account, so registered and unknown emails behave the same. I flagged it in my reply; the user hasn't commented. No recommendations were overridden.
- **Sideways:** Nothing failed. `ruff format` reformatted `accounts/forms.py` (one long line) after it was written. Two limits were noted rather than fixed. First, the in-memory cache is per process: a dev-server restart, including the autoreload on a code change, clears every cooldown, and a production setup running several processes would need a shared cache. Second, the "cache starts empty" test depends on running after the other cooldown tests in file order, so it's a weak check of the fixture. I didn't open the pages in a browser myself; the flow was checked through the test client only.

## 2026-10-07 — Account security Phase 5: password reset by email, plus a readable console mail backend

### Prompts
1. @prd/account-security.md @plans/account-security.md Do Phase 5
2. I would like to manually verify these changes in the browser, how would I do that?
3. Problem. As soon as I open up the reset link, it tells me that the link is no longer valid. Please fix.
4. update PROMPTS.md

### Summary
- **Outcome:** Mounted Django's four built-in reset views under the `accounts` namespace: `password_reset` (`accounts/password-reset/`), `password_reset_done` (`.../sent/`), `password_reset_confirm` (`accounts/reset/<uidb64>/<token>/`), and `password_reset_complete` (`accounts/reset/complete/`). Each one's `success_url` points at the namespaced names. `StyledPasswordResetForm` and `StyledSetPasswordForm` are the stock forms in DaisyUI classes. The stock reset form already matches the email case-insensitively, skips inactive users and users with unusable passwords, and sends nothing for an unknown address while showing the same redirect. Set `PASSWORD_RESET_TIMEOUT = 60 * 60`. Added four site-styled templates. The confirm page shows "This link is no longer valid" with a "Request a new link" button for an expired or used link. Also added a plain-text reset email and subject under `templates/accounts/emails/`, and a "Forgot your password?" link on the sign-in page. Added tests for every Phase 5 acceptance criterion: the sign-in link, a reset in any capitalization opening the set-password form, an unknown email sending nothing with an identical response, signing in with the new password (and not the old), a reused link rejected, the link still valid at 59 minutes and rejected after an hour (via a monkeypatched token clock), and a blank email being refused. Ticked off Phase 5 in `plans/account-security.md`. For prompt 2, gave a browser checklist using the seeded `customer` account (`customer@example.com`), copying the reset link from the runserver terminal. For prompt 3, added `config/mail.py` with `ReadableConsoleEmailBackend`, which prints headers plus the *decoded* body. `EMAIL_BACKEND` now points at it, and a regression test feeds a real reset email through it and opens the printed link. Suite at 311 passed, ruff clean. Nothing committed.
- **Deviations:** Completing a reset does not send a "your password was changed" alert. The plan only ties that alert to the Account-page change. I flagged it as a one-line addition if wanted; the user hasn't decided. No recommendations were overridden.
- **Sideways:** The tests passed, but the reset link was broken in the browser (prompt 3). The link is about 84 characters, and Python's email library encodes any body with a line over 78 characters as quoted-printable. Django's stock console backend prints that raw encoding, so the terminal showed the URL split across two lines with a trailing `=`. A copied link carried a damaged token and was rejected as invalid. The tests missed it because they read links from `mail.outbox`, which never encodes. I reproduced it by printing a reset email through the console backend, then fixed it in the dev backend rather than the reset flow. Real mail clients decode the encoding, so production delivery was never affected. Phase 8 must keep this backend as the console default. Separately, a PowerShell 5.1 one-liner I used to tick the plan's checkboxes re-encoded `plans/account-security.md` and garbled every `—` and `→`. `git diff --stat` caught it (44 changed lines instead of 7); I restored the file from git and ticked the boxes with the Edit tool instead. When piped through Git Bash, the em dashes in the console email showed as `�`, which is a terminal display limit, not a bug.

## 2026-10-07 — Account security Phase 4: change password, with an alert email

### Prompts
1. @prd/account-security.md @plans/account-security.md Do Phase 4
2. I would like to manually check in the browser, how would I do that?
3. Update prompts.md

### Summary
- **Outcome:** Added `accounts:password_change` at `accounts/password/`. It subclasses Django's built-in `PasswordChangeView`, which is already login-required, keeps the current session signed in, and signs out the user's other sessions. On success it redirects to the Account page with a flash message. The new `StyledPasswordChangeForm` is Django's `PasswordChangeForm` in DaisyUI classes, with "Current password" as the first field's label to match the change-email form. New passwords go through the existing four validators. Added `services.notify_password_changed` and a plain-text `emails/password_changed.txt`; accounts with no email get no alert. Added `templates/accounts/password_change.html` and a "Password" card on the Account page. Added tests for: the login redirect, rendering in the site's style, six rejections (wrong current password, mismatch, too short, numeric, common, too similar to the email), the old password failing and the new one working, this session kept while a second `Client` session is signed out, exactly one alert to the account's email, and no alert for a blank-email account. Suite at 301 passed, ruff clean. Ticked off Phase 4's acceptance criteria in `plans/account-security.md`. For prompt 2, gave a browser checklist: seed, sign in as `customer` in a normal window and a private window, try each rejection, change the password, confirm the alert prints in the runserver terminal, and confirm the private window is signed out. Re-seeding restores the demo passwords. Nothing committed.
- **Deviations:** None; Phase 4 was built as the plan described. One small change went outside it: the shared `accounts/partials/_field.html` now wraps help text in a `<div>` instead of a `<p>`, because Django's password help text is a `<ul>`, which isn't valid inside a `<p>`. This matches what `signup.html` already does, and it also affects the address and change-email forms.
- **Sideways:** Nothing failed. `ruff format` reformatted `accounts/tests.py` (one long parametrize row) after it was written. I didn't open the pages in a browser myself; the flows were checked through the test client only. Phases 1–3 were built in earlier sessions that have no log entries here; this entry covers only Phase 4.

## 2026-10-07 — Account security: grill interview and PRD (no code yet)

### Prompts
1. usage
2. `/grill-me` — the website needs updated security features. Customers should provide a email whenever they create an account, they should be able to change their password, and  reset their password through email. Also, if you have any security recomendations, please give them.
3. (Interactive `/grill-me` interview: twelve design questions answered one at a time, covering email uniqueness (unique, case-insensitive), what the login box accepts (username or email), email verification (none), existing blank-email accounts (uniqueness ignores blanks), the Account page (change email + change password), alert emails (password change, and email change to the old address), reset-link lifetime (1 hour), email delivery (console default, SMTP via `.env`), login throttling (django-axes), production hardening (strict settings when DEBUG is off), minimum password length (kept at 8), and reset-request throttling (per-email 5-minute cooldown).)
4. `/to-prd`
5. Append a session log to PROMPTS.md at the repo root, under today's date, newest entry at the top. Record every prompt I gave you this session, in order, including any corrections. End the entry with a short summary: the outcome, any places where I deviated from a recommended answer or asked follow-up questions, and anything that went sideways.

### Summary
- **Outcome:** Before the interview, read the accounts app, settings, and seed command. That answered several questions from the code instead of asking: signup has no email field on purpose, `AbstractUser.email` is optional and non-unique, the seed already gives every demo user an email, email uses the console backend, and none of the password change/reset views exist yet. The interview produced a 12-point plan, and `/to-prd` turned it into `prd/account-security.md`. It has 27 user stories, the design decisions, what's out of scope, and a list of what the tests should cover. It notes that it overrides the core-platform PRD's "no email at signup" decision. No application code was changed, nothing was committed, and the PRD is untracked.
- **Deviations:** Question 11 (minimum password length) overrode my recommendation of 12 characters; it stays at Django's default of 8. Every other question took the recommended option. No follow-up questions were asked during the interview.
- **Sideways:** Prompt 1 ("usage") was ambiguous. I answered both ways: pointing to the built-in `/usage` command, and listing the project's commands from CLAUDE.md. The PRD also includes two items the user never voted on, which I had listed at the end of the interview as additions I'd make without asking: a configurable admin URL instead of `/admin/`, and the list of tests to write. I flagged both in my reply so they can be cut. The untracked `.claude/skills/to-prd/` folder existed before this session and was left alone.

## 2026-10-03 — Product images follow-up: manual verification, cart/order images removed, tracing an upload

Continues the same session as the entry below, which logged prompts 1–3.

### Prompts
4. how can I manually check in the browser that all implemented features are working?
5. Everything looks great except in the cart, let's just not show images in the cart or order history.
6. (Outside Claude Code — Grok, around 2:15 PM, per the user) generate an image of a watermellon robot
7. where is the image field you created and where is the <form> used to upload a product image.
8. Tell me 1. The path where the image file is stored on disk. 2.The value stored in the database for that image. 3.The URL the browser requests to display it. for the image called h1kJJ.jpg
9. Try again.
10. Ok, last prompt for the day, append a session log for PROMPTS.md. Also add a prompt around 2:15 from Grok with the prompt "generate an image of a watermellon robot". Thank you.

### Summary
- **Outcome:** Gave a step-by-step browser checklist, including a script that writes one test file per rejection rule into `test-uploads/` and commands that simulate a missing and a broken image file. Per prompt 5, removed product images from the cart and from both order-detail pages (customer and back office) by restoring those templates, `orders/models.py`, and `orders/views.py` to their committed versions. Those files held only the image changes, as `git diff --stat` confirmed first. Deleted the order-line image test and flipped the cart test to assert the cart shows *no* product images. Suite at 256 passed, ruff clean. Pointed to the image field (`products/models.py:82`), the upload form class (`ProductImageForm`, `products/forms.py:61`), and the multipart `<form>` (`templates/products/manage_product_form.html:49`). Traced `h1kJJ.jpg`, the Grok image from prompt 6 downloaded to the user's Downloads folder: it was uploaded to the product with slug `Watermellon_robot` and stored at `media\products\Watermellon_robot.webp`, as DB value `products/Watermellon_robot.webp`, served at `/media/products/Watermellon_robot.webp`. A pixel comparison matched the two (784×1168, mean difference 1.72/255, from WebP compression).
- **Deviations:** Prompt 5 reversed part of the earlier grill answer (images in the cart and order history), which had itself gone beyond my recommendation of back-office list only. The entry below still describes those images as shipped; it is left as written, per this file's rules, and this entry records the reversal. Pointed out that the `Watermellon_robot` slug breaks the lowercase-hyphen convention the other slugs follow; left it unchanged.
- **Sideways:** My first answer to prompt 8 was wrong in substance. I searched only for files and database values named `h1kJJ`, found none, and answered with a hypothetical ("Pulse Halo") instead of looking for a recent upload under a different name. Prompt 9 ("Try again") caught it; a wider search found the file in Downloads and the newly uploaded product image, and a pixel comparison confirmed the match. The VS Code Pylance warnings (`pytest`/`PIL` "could not be resolved") came from the editor not using the project's `.venv` interpreter, not from the code. The Downloads copy of `h1kJJ.jpg` has a modified time of 1:41 PM, earlier than the approximate 2:15 PM given for the Grok prompt; the time is recorded as the user stated it.

## 2026-10-03 — Product photos from the product-images folder, plus validated back-office uploads

### Prompts
1. `/grill-me` — Replace all avalible item placeholder images with appropriate images found in the product-images folder. If an item does not have a image in the product-images folder,or if the image is missing/broken continue using the placeholder. Employees will also be allowed to upload images for items using the back office. If an employee uploads a file the website cannot use, reject and explain the problem in plain english, do not accept the file first then lose it.
2. (Interactive `/grill-me` interview: thirteen design questions answered one at a time, covering storage model (one `Product.image` field), folder-to-product matching (explicit list), which product gets the SoulSear image (Mark I), SyncRest text-vs-plain variant (plain), sibling-image borrowing (exact matches only), missing/broken fallback layering (server check + `onerror`), resizing (fit 1200 px, WebP), rejection rules, the "accept then lose" upload flow (separate image form), git handling of the source images, catalog card shape (4:3 crop), where else images appear, and which image old order lines show (the live product's). See Deviations for the two answers that went beyond my recommendation.)
3. implement, after implementation write in the session log with a standard prompt in PROMPTS.md header

### Summary
- **Outcome:** Added Pillow, `MEDIA_ROOT`/`MEDIA_URL` (with `media/` gitignored and served while DEBUG), and an optional `Product.image` (migration `0004_product_image`). New `products/images.py` holds the single rule set: `validate_product_image` (JPG/PNG/WebP only, 10 MB cap, at least 400 px on the shortest side, a guard against huge pixel dimensions, and an "unreadable/damaged" catch-all, each with a plain-English message) and `to_webp` (fit within 1200 px, honor EXIF rotation, keep transparency). `Product` gained `has_image`, `placeholder_url`, `display_image_url`, `replace_image` (old file deleted only after the new one saves) and `remove_image`, plus a `post_delete` receiver that removes a deleted product's file. `OrderItem` gained matching image properties that follow the live product and fall back to `default.svg` when the product is gone. The back-office edit page has a separate image panel (`ProductImageForm`, POST-only upload and remove views), so only image errors can reject an upload and a valid file is never dropped over an unrelated field error. New products now land on their edit page to add an image. The 12 used source images moved to `products/seed_images/` with tidy names, and `seed` validates and attaches them through the same rules, warning (not failing) on a missing or bad file and emptying `media/products/` first. Images render through one `_image.html` partial (server fallback plus `onerror`) on the catalog (4:3 `object-cover` frame), detail page (full image), back-office list (thumbnail plus "No photo" badge), cart, and both order-detail pages. The Django admin shows the image read-only so uploads can't skip validation. Added 32 tests and an autouse `media_root` fixture; full suite 257 passed, ruff clean. The seed reports "34 products (12 with photos)", stored files shrank from about 2 MB PNGs to 55–220 KB WebPs, and re-seeding leaves exactly 12 files. Verified against the live dev server: photos served as `image/webp`, Mark II keeps its placeholder, GIF/tiny/fake-PDF uploads each rejected with their plain-English message, a 2400×1800 JPG accepted and stored at 1200×900, and Remove restores the placeholder. Updated `docs/TESTING.md` and `docs/TEMPLATES.md`.
- **Deviations:** Two answers went beyond my recommendation: the minimum-size rule (400 px shortest side) was added even though I advised leaving it out, and images were extended to the cart and order history rather than just the back-office list. Order history then needed a follow-up question, answered with my recommendation (the live product's image, no checkout snapshot). Everything else followed the recommended option.
- **Sideways:** I recommended the `onerror` fallback after checking only for a Content-Security-Policy, and found during implementation that `docs/TEMPLATES.md` says "no JavaScript beyond HTMX". I kept the answer as chosen and recorded it in TEMPLATES.md as the one sanctioned exception rather than silently breaking the rule. A PowerShell one-liner I used to fix an import re-read `test_images.py` in the wrong encoding and garbled a `×` into `Ã—`; the resulting test failure caught it, and a scan confirmed it was the only damaged character. A check that the `aspect-[4/3]` class compiled first reported it missing, which was just my search pattern being escaped wrong; the class was there. The unused `SyncRest GPT Text.png` was left untracked in `product-images/` rather than deleted. I didn't look at the pages visually in a browser; layout was checked via the rendered HTML and compiled CSS only.

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
