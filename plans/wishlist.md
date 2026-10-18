# Plan: The ThoughtTronix Store — Customer Wishlist

> Source PRD: `prd/wishlist.md`. The PRD owns the requirements; this plan owns
> the sequence. Where the two disagree, the PRD wins.

## Architectural decisions

Durable decisions that apply across all phases:

- **Owning app**: a new, self-contained `wishlist` app with its own models,
  views, URL namespace, templates (`templates/wishlist/`, partials under
  `templates/wishlist/partials/`), and tests. It depends on `products` and the
  user model. Other apps touch it only through the product detail page
  including its button and the navbar linking to its page.
- **URLs** (namespace `wishlist`, mounted at the project root like `orders`):
  - `wishlist/` → `wishlist:detail`: the signed-in user's wishlist page (GET)
  - `wishlist/add/<int:pk>/` → `wishlist:add`: POST-only, by **product** pk;
    renders the button partial
  - `wishlist/remove/<int:pk>/` → `wishlist:remove`: POST-only, by
    **product** pk; renders the button partial
  - `wishlist/items/<int:pk>/remove/` → `wishlist:remove_item`: POST-only, by
    **product** pk, resolved through the signed-in user's own wishlist;
    re-renders the list partial
  - No wishlist or wishlist-item identifier ever appears in a URL. The
    wishlist is always resolved from `request.user`.
- **Models**:
  - `Wishlist`: `OneToOneField` to the user (`CASCADE`). It has no name and no
    sharing fields. `Wishlist.for_user(user)` gets the wishlist or creates it on
    first touch, the same lazy pattern as `Cart.for_user`.
  - `WishlistItem`: FK to `Wishlist` (`CASCADE`), FK to `Product` (`CASCADE`),
    and an `added_at` timestamp. A `UniqueConstraint` on (wishlist, product)
    allows each product once per wishlist. Default ordering is `-added_at`.
  - Model methods own the logic: `add(product)`, `remove(product)`, and
    `contains(product)`. Add and remove are idempotent no-ops when there is
    nothing to do. No service module, since nothing crosses models.
- **Product lookups**: add and remove look products up in the full
  `Product` set, not the "available" filter, so unavailable products can be
  saved. A nonexistent pk returns 404.
- **Authorization**: every wishlist view requires sign-in (`LoginRequiredMixin`).
  Every signed-in user (customer, staff, or superuser) has their own wishlist,
  with no role checks.
- **Admin**: the wishlist models are deliberately **not** registered in the
  Django admin, and there is no back-office tab. The model docstring says so
  explicitly, so nobody later "fixes" the omission.
- **HTMX**: the detail-page button swaps itself (`outerHTML`). The
  wishlist-page Remove swaps the list partial. There are no out-of-band swaps.
  Anonymous visitors get a plain sign-in link carrying `next`, with no HTMX,
  mirroring the add-to-cart button. CSRF already reaches HTMX through
  `base.html`.
- **Testing**: pytest + pytest-django in `wishlist/tests`, using the shared
  fixtures (`customer`, `staff_user`, `product`, `unavailable_product`, …).
  Any new shared fixture (e.g. `wishlist`) goes in the project-level
  `conftest.py`. The suite is green and Ruff is clean at every phase
  boundary.

---

## Phase 1: Save a product from its detail page

**User stories**: 1, 2, 4, 5, 6, 7, 11, 19 (button side), 20, 22, 23

### What to build

Create the `wishlist` app, register it in settings, and add both models with
their migration, the lazy `for_user` accessor, `add`, and `contains`. Don't
register them in the admin, and give `Wishlist` a docstring explaining why.
Add the POST-only `wishlist:add` endpoint, which saves the product for the
signed-in user and responds with the button partial. Include the partial on
the product detail page next to the add-to-cart button. The detail page knows
whether the product is already saved for the signed-in user. The partial
renders three states:

- a signed-in, unsaved product: an HTMX button posting to add, labelled "Add to wishlist"
- a signed-in, saved product: a static "On your wishlist" state (Phase 2 makes it a remove button)
- an anonymous visitor: a plain sign-in link carrying `next`

### Acceptance criteria

- [x] `Wishlist.for_user` creates a wishlist on first call and returns the same one afterwards; each user has exactly one.
- [x] `add` saves a product, and a repeat `add` keeps a single entry.
- [x] The database rejects a duplicate (wishlist, product) pair.
- [x] `contains` reports the saved status correctly.
- [x] Deleting a product deletes its wishlist items, and deleting a user deletes their wishlist.
- [x] `wishlist:add` is POST-only (GET → 405), returns 404 for a missing product, and redirects anonymous requests to sign-in.
- [x] An unavailable product can be saved.
- [x] The detail page shows the right button state and label for unsaved, saved, and anonymous.
- [x] One user's add never affects another user's wishlist.
- [x] Staff users get their own wishlist like anyone else.
- [x] Neither wishlist model is registered with the admin site.
- [x] The catalog grid is unchanged.
- [x] The suite is green and Ruff is clean.

---

## Phase 2: Remove from the detail page

**User stories**: 8, 9, 10

### What to build

Add `remove` to the model and a POST-only `wishlist:remove` endpoint that
responds with the button partial. The saved state of the button becomes an
HTMX button posting to remove, labelled "On your wishlist — remove". Each
endpoint returns the product's actual saved state after the operation. A
double-click, or a stale second tab, therefore always redraws the button
correctly.

### Acceptance criteria

- [x] `remove` deletes a saved product, and removing an unsaved product is a no-op.
- [x] `wishlist:remove` is POST-only, returns 404 for a missing product, and redirects anonymous requests to sign-in.
- [x] Adding twice leaves one entry. Removing twice leaves it removed. Each response renders the true state.
- [x] The saved-state button posts to remove, and the unsaved-state button posts to add.
- [x] One user's remove never affects another user's wishlist.
- [x] The suite is green and Ruff is clean.

---

## Phase 3: The wishlist page

**User stories**: 3, 12, 13, 14, 15, 16, 18, 21

### What to build

Add `wishlist:detail`, a sign-in-required page extending `base.html` that
lists the signed-in user's items newest first, with their products loaded.
The list lives in its own partial so Phase 4 can swap it. Each row shows the
product image (through `products/partials/_image.html`), its name linked to
the detail page, its price, and an "Unavailable" badge where it applies. An
empty wishlist shows a designed empty state that links back to the catalog.
Add a plain "Wishlist" text link to the navbar for signed-in users, next to
Orders and Addresses, with no count badge. Use Tailwind + DaisyUI and follow
`docs/TEMPLATES.md`.

### Acceptance criteria

- [x] Anonymous visitors to `wishlist:detail` are redirected to sign-in.
- [x] The page lists only the signed-in user's items, newest first.
- [x] Each row shows the image, a linked name, and the current price. Unavailable products show the "Unavailable" badge.
- [x] A product the store deletes no longer appears.
- [x] An empty wishlist renders the empty state with a catalog link.
- [x] The navbar shows the Wishlist link only to signed-in users.
- [x] The page avoids N+1 queries for products.
- [x] The suite is green and Ruff is clean.

---

## Phase 4: Remove from the wishlist page

**User stories**: 17, 19 (page side)

### What to build

Each row on the wishlist page gets a Remove button that posts to
`wishlist:remove_item` and swaps the list partial in place. The view looks the
product up through the signed-in user's own wishlist, so an entry belonging
to someone else can never be touched. Removing the last item renders the
empty state.

### Acceptance criteria

- [x] `wishlist:remove_item` is POST-only and redirects anonymous requests to sign-in.
- [x] A successful removal returns the list partial (not the full page) without the removed item.
- [x] Removing the last item returns the empty state.
- [x] A request naming a product saved only on another user's wishlist leaves that wishlist unchanged.
- [x] The suite is green and Ruff is clean.

---

## Phase 5: Seed the demo wishlist

**User stories**: 24, 25

### What to build

The `seed` command wipes wishlists along with the rest of the demo data. It
then gives the demo `customer` user a wishlist of two or three products, at
least one of them unavailable, and its summary output mentions the wishlist.
Append this feature's AI-usage entries to `PROMPTS.md`.

### Acceptance criteria

- [ ] After `seed`, `customer` has 2–3 wishlist items, at least one of them an unavailable product.
- [ ] Running `seed` twice produces the same wishlist with no duplicates or errors.
- [ ] `PROMPTS.md` has this feature's entries appended.
- [ ] The suite is green and Ruff is clean.
