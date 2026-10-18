# PRD: The ThoughtTronix Store — Customer Wishlist

*Commissioned by ThoughtTronix Product Management. "Your Thoughts, Our Business."*

---

## Problem Statement

A customer browsing the store who finds a product they want — but not today — has nowhere to put it. The only place to keep a product is the cart, and the cart means "I am buying this": it carries quantities, totals, and a checkout button, and a customer who parks products there to remember them ends up with a cart that no longer reflects what they mean to buy. A product that is currently unavailable can't go in the cart at all, so the customer who wants it when it returns has to remember it on their own.

The customer needs a private, low-commitment list of products they are interested in, that they can add to and take from in a single click while looking at a product, and that no one else can see.

## Solution

Every signed-in customer has exactly one **Wishlist**. It has no name to edit and no way to share it — it is simply "my wishlist."

On a product's detail page, alongside the add-to-cart button, a wishlist button shows whether the product is already saved. Clicking it adds or removes the product in place, without reloading the page, and the button immediately redraws to show the product's real current status. Any product can be saved, including one that is currently unavailable.

A **Wishlist** link in the navbar takes the customer to their wishlist page, which lists everything they have saved, newest first, with each product's image, name, price, and an "Unavailable" badge where it applies. Each entry has a Remove button that takes it off the list in place. An empty wishlist shows a designed empty state rather than a blank page.

Visitors who are not signed in see a wishlist button that takes them to sign in and then back to the product. A customer can only ever see and change their own wishlist — there is no address, link, or back-office screen through which anyone else's wishlist can be reached.

## User Stories

**Visitor (not signed in)**

1. As a visitor, I want to see a wishlist button on a product's detail page, so that I know the store lets me save products for later.
2. As a visitor, I want clicking the wishlist button to take me to sign in and then return me to the same product, so that I can save it without hunting for it again.
3. As a visitor, I want the wishlist page to send me to sign in, so that I understand a wishlist belongs to an account.

**Customer (signed in)**

4. As a customer, I want a wishlist that exists without my having to create it, so that saving my first product just works.
5. As a customer, I want exactly one wishlist, so that I always know where my saved products are.
6. As a customer, I want the wishlist button on a product's detail page to show whether that product is already on my wishlist, so that I don't have to check the list.
7. As a customer, I want to add a product to my wishlist from its detail page without the page reloading, so that I don't lose my place.
8. As a customer, I want to remove a product from my wishlist from its detail page without the page reloading, so that I can change my mind just as easily.
9. As a customer, I want the button to redraw immediately after I click it to show the product's actual saved status, so that I can trust what it says.
10. As a customer who double-clicks the button or has the product open in two tabs, I want the result to still be correct — saving twice keeps one entry, removing twice leaves it removed — so that the button never ends up lying to me.
11. As a customer, I want to be able to save a product that is currently unavailable, so that I can remember to buy it when it returns.
12. As a customer, I want a Wishlist link in the navbar, so that I can reach my saved products from any page.
13. As a customer, I want my wishlist page to list my saved products newest first, so that what I just saved is at the top.
14. As a customer, I want each saved product to show its image, name, and current price, so that I can recognise and compare them at a glance.
15. As a customer, I want each saved product's name to link to its detail page, so that I can go look at it or buy it.
16. As a customer, I want saved products that are no longer available to be clearly marked "Unavailable," so that I am not surprised when I try to buy one.
17. As a customer, I want to remove a product from my wishlist page without the page reloading, so that tidying my list is quick.
18. As a customer with nothing saved, I want a friendly empty state that points me back to the catalog, so that the page isn't just blank.
19. As a customer, I want my wishlist to be private, so that no other customer can see or change what I've saved.
20. As a customer, I want there to be no way to rename or share my wishlist, so that it stays a simple personal list.
21. As a customer, I want a product that the store deletes to quietly disappear from my wishlist, so that I'm never shown a broken entry.

**Employee (staff)**

22. As an employee, I want my own wishlist like any other shopper, so that I can use the store the same way customers do.
23. As an employee, I want no back-office or admin screen exposing customers' wishlists, so that customers' private interests stay private.

**Developer / demo**

24. As someone demoing the store, I want the seeded demo customer to already have a few products on their wishlist — including one unavailable product — so that the wishlist page and its "Unavailable" badge can be shown without setup.
25. As a developer, I want reseeding to reset wishlists along with everything else, so that the seed stays idempotent.

## Implementation Decisions

**A new app**

- The feature lives in a new, self-contained `wishlist` app with its own models, views, URL namespace, templates, and tests. It depends on `products` and on the user model; nothing in other apps depends on it beyond the detail page including its button and the navbar linking to it.

**Models**

- `Wishlist` — a one-to-one link to the user (deleting the user deletes the wishlist). It deliberately has no name field and no sharing fields. A class-level "for user" accessor returns the user's wishlist, creating it on first touch — the same lazy pattern the cart uses.
- `WishlistItem` — belongs to a wishlist and a product, with an "added at" timestamp. A database uniqueness constraint on the wishlist–product pair guarantees a product is saved at most once. Default ordering is newest first. Deleting a product deletes its wishlist items (cascade).
- Model methods own the logic, keeping views thin:
  - **add(product)** — saves the product if it isn't already saved; a repeat add is a no-op.
  - **remove(product)** — removes the product if it is saved; removing an unsaved product is a no-op.
  - **contains(product)** — whether the product is currently saved.
- No service module is needed: every operation touches only the wishlist and its items.

**Access and privacy**

- Every wishlist view requires sign-in. The wishlist is always resolved from the signed-in user; no wishlist or wishlist-item identifier ever appears in a URL, so there is nothing to tamper with to reach another person's list.
- Every signed-in user — customer, staff, or superuser — has their own wishlist. No role checks.
- The wishlist models are intentionally **not** registered in the Django admin, and there is no back-office tab. This differs from the cart and address book, which are in the admin; the model docstring must say so explicitly so the omission isn't later "fixed."

**URLs and views**

- Wishlist page — a GET at the wishlist's root, listing the signed-in user's items with their products loaded.
- Add — POST-only, by product pk. Renders the wishlist button partial showing the new state.
- Remove (from the detail page) — POST-only, by product pk. Renders the wishlist button partial showing the new state.
- Separate add and remove endpoints were chosen over a single toggle so each request is idempotent; the response always reflects the true saved state, which keeps the button correct under double-clicks and stale tabs.
- Product lookups for add and remove use the full product set, not the "available" filter — unavailable products can be saved. A nonexistent product pk is a 404.
- Remove from the wishlist page — POST-only, re-renders the wishlist list partial (not the whole page). It identifies the entry through the signed-in user's own wishlist, never by a bare pk.

**HTMX interactions**

- The detail-page button is an HTMX partial that replaces itself (outer swap) with the server's response. When the product is saved it posts to remove; when not saved it posts to add. Labels make the state obvious (e.g. "Add to wishlist" vs. "On your wishlist — remove").
- For anonymous visitors the button is a plain link to sign in carrying a `next` back to the current page — no HTMX — mirroring the add-to-cart button.
- The wishlist page's Remove button swaps the list partial in place. Removing the last item shows the empty state.
- No out-of-band swaps: neither response updates anything outside its own target.
- Partials follow the project's convention: underscore-prefixed, under the app's partials folder, never extending the base template. CSRF is already supplied to HTMX by the base template.

**Templates**

- Product detail page: include the wishlist button next to the add-to-cart button. The detail view (or the template, via the wishlist) provides whether the product is saved for the signed-in user. The catalog grid is unchanged.
- Navbar: a plain "Wishlist" text link for signed-in users, alongside Orders and Addresses. No count badge.
- Wishlist page: extends the base template; each row shows image (through the existing product image partial), linked name, price, an "Unavailable" badge where applicable, and Remove. Designed empty state linking back to the catalog. Tailwind + DaisyUI only, Times New Roman per the template conventions.

**Seed**

- The seed command wipes wishlists along with the other demo data and gives the demo `customer` user a wishlist of two or three products, at least one of them unavailable.

**Testing**

- pytest + pytest-django in the app's tests module, using the shared plain fixtures (`customer`, `staff_user`, `product`, `unavailable_product`, …); any new shared fixture (e.g. a wishlist) goes in the project-level conftest.
- Cover: lazy creation and one-per-user; add is idempotent; remove is idempotent; contains; uniqueness constraint; newest-first ordering; product deletion cascades; anonymous requests redirect to sign-in; add/remove are POST-only and 404 on a missing product; unavailable products can be saved; button partial renders the right state and label for saved, unsaved, and anonymous; one user's add/remove never affects another user's wishlist; wishlist-page removal can't touch another user's item; empty state renders; navbar link shown only when signed in; wishlist models absent from the admin; seed creates the demo wishlist and reseeding is idempotent.
- The suite must be green at every phase boundary.

## Out of Scope

- Multiple wishlists per customer, named wishlists, or renaming.
- Sharing a wishlist, public wishlist links, or gift registries.
- Any staff, back-office, or Django-admin view of wishlists.
- A wishlist button on catalog grid cards (the button partial is reusable, so this is a later one-line addition).
- Add-to-cart or "move to cart" from the wishlist page.
- A wishlist item-count badge in the navbar.
- Notes, priorities, or quantities on wishlist items.
- Notifications when a saved product returns to stock or changes price.
- Wishlists for anonymous visitors (e.g. session-based) or merging them at sign-in.
- Wishlist analytics on the staff dashboard.

## Further Notes

- The design deliberately mirrors the cart (one-per-user model created lazily, item model with a uniqueness constraint, HTMX partials, ownership through the signed-in user) so the codebase stays predictable. The one intentional divergence is the absence of admin registration, chosen to honour "customers can only access their own wishlist" strictly.
- Because a product can become unavailable after it is saved, the wishlist page must handle unavailable products regardless; that is why saving unavailable products is allowed rather than blocked.
- Remember to append this feature's AI-usage entries to `PROMPTS.md`, per the project rules.
