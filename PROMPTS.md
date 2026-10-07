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
