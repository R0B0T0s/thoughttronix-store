# Plan: The ThoughtTronix Store — Product Reviews

> Source PRD: `prd/reviews.md`. The PRD owns the requirements; this plan owns
> the sequence. Where the two disagree, the PRD wins.

## Architectural decisions

Durable decisions that apply across all phases:

- **Owning app**: a new, self-contained `reviews` app with its own models,
  views, forms, URL namespace, templates (`templates/reviews/`, partials under
  `templates/reviews/partials/`), and tests. It depends on `products`, the
  user model, and one read-only query in `orders`. Other apps touch it only
  through the product detail page including its section. `orders` never
  imports from `reviews`.
- **URLs** (namespace `reviews`, mounted at the project root like `wishlist`):
  - `reviews/product/<int:pk>/` → `reviews:section`: GET, by **product** pk;
    renders the Reviews section partial for anyone. Cancel-edit reuses it.
  - `reviews/product/<int:pk>/create/` → `reviews:create`: POST-only,
    sign-in required, by **product** pk.
  - `reviews/<int:pk>/edit/` → `reviews:edit`: by **review** pk, sign-in
    required. GET returns the section with the in-place, pre-filled form;
    POST saves the edit.
  - `reviews/<int:pk>/delete/` → `reviews:delete`: POST-only, sign-in
    required, by **review** pk.
  - Every response re-renders the whole Reviews section partial for the
    product. A nonexistent product or review is a 404. Product lookups use
    the full `Product` set, not the "available" filter, so unavailable
    products can be reviewed.
- **Models**:
  - `Review`: FK to the user (`CASCADE`), FK to `Product` (`CASCADE`),
    `rating` (small positive integer, `CheckConstraint` 1–5), `comment`
    (blank allowed, max ~2,000 characters), `created_at`, `updated_at`, and
    `edited_by_staff` (boolean). A `UniqueConstraint` on (user, product)
    gives one review per customer per product. Default ordering is newest
    first.
  - Model methods own the logic: `can_review(user, product)` (class-level),
    `author_edit(rating, comment)`, `staff_edit(comment)`, `was_edited`,
    `can_change(user)`, and the reviewer display name (first name + last
    initial, falling back to username). The product rating summary (average
    to one decimal, plus count) is a queryset aggregation, not a stored
    field.
- **The purchase rule**: a queryset method on `OrderItem` in `orders` —
  the user has an order line for the product on an order whose status is not
  `CANCELLED`. Checked only on **create**; later cancellation never hides,
  locks, or deletes a review. No service module.
- **Authorization**: `LoginRequiredMixin` on every write and edit endpoint
  (anonymous → redirect to sign-in). Create: signed in, purchased, not
  already reviewed — staff follow the same rule. Author edit: rating and
  comment. Staff edit of another user's review: comment only, sets
  `edited_by_staff`; staff editing their own review are treated as the
  author. Delete: author or any staff. Anyone else signed in gets 403.
  Staff is `is_staff` — no role field, no Groups.
- **Forms**: an author form (rating required, comment optional and
  length-limited) and a staff moderation form (comment only). Invalid
  submissions re-render the section with errors and input preserved.
- **HTMX**: the whole section (summary, "Your review" box, list) is one
  partial and one swap target, replaced on every response. No out-of-band
  swaps. Delete buttons use `hx-confirm="Delete this review?"`. Anonymous
  visitors get a plain sign-in link carrying `next` back to the product, no
  HTMX. CSRF already reaches HTMX through `base.html`.
- **Templates**: stars render through a reusable star partial using
  DaisyUI's rating component (radio inputs in forms, read-only for display).
  Tailwind + DaisyUI, following `docs/TEMPLATES.md`. The catalog grid is
  unchanged.
- **Admin**: `Review` is registered in the Django admin, listing reviewer,
  product, rating, dates, and the staff flag.
- **Testing**: pytest + pytest-django in `reviews/tests`, using the shared
  fixtures (`customer`, `staff_user`, `product`, `unavailable_product`, …).
  New shared fixtures (e.g. a purchased product or a review) go in the
  project-level `conftest.py`. The suite is green and Ruff is clean at every
  phase boundary.

---

## Phase 1: The read-only Reviews section

**User stories**: 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 36, 41

### What to build

Create the `reviews` app, register it in settings, and add `Review` with its
migration and both database constraints. Add the purchase query to `orders`.
Add the display name, `was_edited`, and the product rating summary. Register
`Review` in the admin. Include the Reviews section partial on the product
detail page below the product information, showing:

- the summary (average stars and count), or "No reviews yet — be the first"
- the "Your review" box in its two non-form states: a "Sign in to review
  this product" link carrying `next` (anonymous), and "Only customers who've
  purchased this product can review it" (signed in, not purchased)
- every review newest first, each with display name, "Verified purchase"
  badge, read-only stars, comment if present, posted date, and "(edited)" /
  "Edited by staff" markers when applicable

Build the reusable star partial. Reviews in this phase are created directly
in tests.

### Acceptance criteria

- [ ] The purchase query counts placed, shipped, and delivered orders, and ignores cancelled orders, no orders, and other users' orders.
- [ ] The database rejects a duplicate (user, product) review and a rating outside 1–5.
- [ ] Deleting a product or a user deletes their reviews.
- [ ] The display name is first name + last initial, falling back to the username.
- [ ] `was_edited` is false for a fresh review and true after a meaningful later update.
- [ ] The summary gives the average to one decimal and the count, and handles no reviews.
- [ ] The detail page shows the summary or the empty state, and lists reviews newest first with badge, stars, comment, date, and markers when applicable.
- [ ] The "Your review" box shows the sign-in link (with `next` back to the product) for anonymous visitors and the purchasers-only note for signed-in non-purchasers.
- [ ] `Review` is registered in the admin.
- [ ] The catalog grid is unchanged.
- [ ] The suite is green and Ruff is clean.

---

## Phase 2: Post a review

**User stories**: 13, 14, 15, 16, 17, 18, 19, 20, 27 (post), 29

### What to build

Add `can_review` and the author form. Add `reviews:section` and the
POST-only `reviews:create`, which enforces the purchase rule on the server
and responds with the re-rendered section. The "Your review" box gains two
states: an HTMX empty form (star radios + comment) for an eligible user, and
the user's own posted review pinned in the box (other reviews still list
below it). Invalid input re-renders the form with errors and the user's
input preserved. A duplicate create — double-submit or stale tab — doesn't
error; it renders the section showing the existing review.

### Acceptance criteria

- [ ] `can_review` is true only for a signed-in purchaser who hasn't reviewed the product.
- [ ] `reviews:create` is POST-only, 404s on a missing product, and redirects anonymous requests to sign-in.
- [ ] A non-purchaser (including one whose only order is cancelled) can't create a review.
- [ ] A purchaser can review an unavailable product.
- [ ] Rating is required and must be 1–5; comment is optional and length-limited; errors re-render with input preserved.
- [ ] A second create from the same user leaves one review and renders it without error.
- [ ] After posting, the box shows the user's review and the summary reflects it.
- [ ] Staff follow the same purchase rule for their own reviews.
- [ ] `reviews:section` renders the section partial (not the full page) for anyone.
- [ ] The suite is green and Ruff is clean.

---

## Phase 3: Author edit and cancel

**User stories**: 21, 22, 23, 24, 27 (edit), 28 (edit)

### What to build

Add `author_edit` and `can_change`. Add `reviews:edit`: GET swaps the
author's pinned box to a pre-filled author form in place; POST applies the
edit, clearing the staff flag, and re-renders the section. The form's Cancel
button re-fetches `reviews:section`. The author's posted review gains an
Edit button. Reviews remain editable even if the underlying order is later
cancelled.

### Acceptance criteria

- [ ] `author_edit` updates rating and comment and clears `edited_by_staff`.
- [ ] `can_change` is true for the author (and staff), false for other customers.
- [ ] GET `reviews:edit` returns the section with a pre-filled author form; POST saves and returns the updated section with "(edited)".
- [ ] Invalid edits re-render with errors and input preserved.
- [ ] Cancel returns the section with the review unchanged.
- [ ] A review stays editable after its order is cancelled.
- [ ] Another customer gets 403 on GET and POST; anonymous requests redirect to sign-in; a missing review is 404.
- [ ] The suite is green and Ruff is clean.

---

## Phase 4: Delete a review

**User stories**: 25, 26, 27 (delete), 28 (delete), 34

### What to build

Add the POST-only `reviews:delete`, allowed for the author or any staff
member. The author's posted review gains a Delete button, and staff see
Delete on every review; each carries `hx-confirm="Delete this review?"`. On
success the section re-renders — for the author, the empty form returns and
the summary updates.

### Acceptance criteria

- [ ] `reviews:delete` is POST-only, redirects anonymous requests to sign-in, and 404s on a missing review.
- [ ] The author can delete their review; the response shows the empty form and an updated summary.
- [ ] Staff can delete any review.
- [ ] Another customer gets 403 and the review survives.
- [ ] Every Delete button carries the confirmation.
- [ ] Delete buttons render only for users allowed to change the review.
- [ ] The suite is green and Ruff is clean.

---

## Phase 5: Staff moderation edit

**User stories**: 30, 31, 32, 33, 35

### What to build

Add `staff_edit` and the comment-only staff form. Staff see Edit on every
review in the list. For another user's review, `reviews:edit` GET swaps that
review's card to the staff form in place, and POST updates only the comment
and sets "Edited by staff." Staff editing their own review get the normal
author form and are treated as the author.

### Acceptance criteria

- [ ] `staff_edit` changes only the comment and sets `edited_by_staff`; the rating never changes.
- [ ] Staff editing another user's review get the comment-only form; a posted rating is ignored.
- [ ] The edited review shows "Edited by staff."
- [ ] Staff editing their own review get the full author form, and saving clears the staff flag.
- [ ] Customers never see Edit on others' reviews.
- [ ] The suite is green and Ruff is clean.

---

## Phase 6: Seed the demo reviews

**User stories**: 37, 38, 39, 40

### What to build

The `seed` command wipes reviews along with the rest of the demo data, then
creates a realistic spread: several seeded users reviewing several products,
mixed 1–5 ratings, some with comments and some without, one marked "Edited
by staff." Every seeded review is backed by a real non-cancelled order for
that user and product. The demo `customer` has reviewed one purchased
product and has at least one other purchased product not yet reviewed. The
seed's summary output mentions reviews. Append this feature's AI-usage
entries to `PROMPTS.md`.

### Acceptance criteria

- [ ] After `seed`, reviews exist with mixed ratings, some without comments, and exactly one marked "Edited by staff."
- [ ] Every seeded review is backed by a non-cancelled order for that user and product.
- [ ] `customer` has one review and at least one purchased, unreviewed product.
- [ ] Running `seed` twice produces the same reviews with no duplicates or errors.
- [ ] `PROMPTS.md` has this feature's entries appended.
- [ ] The suite is green and Ruff is clean.
