111# PRD: The ThoughtTronix Store — Product Reviews

*Commissioned by ThoughtTronix Product Management. "Your Thoughts, Our Business."*

---

## Problem Statement

A shopper looking at a product has only the store's own word for it: the tagline, the description, and the price. There is no way to hear from the people who actually bought it, and no way for a customer who bought something to tell others what they thought. Customers who loved a product can't recommend it, customers who regretted it can't warn anyone, and new shoppers can't tell a well-loved product from a dud.

Any review system also has to be trustworthy. A review should come from someone who really bought the product, each customer should get one voice per product, and the store must not be able to quietly rewrite what customers said. Writing, fixing, or removing a review must also be painless: a customer partway down a product page should never be bounced to another page or lose their place.

## Solution

Every product's detail page gains a **Reviews** section below the product information. At the top is a summary — average stars and review count — or a friendly "No reviews yet — be the first" when there are none.

Beneath the summary is a pinned **Your review** box. A signed-in customer who has bought the product sees a form to give it 1 to 5 stars and, optionally, a written comment. Once posted, the box shows their review with Edit and Delete buttons. Edit turns the box into a pre-filled form in place; Delete asks "Delete this review?" and, on confirmation, the empty form returns. A visitor who isn't signed in sees a link to sign in and come back; a signed-in customer who hasn't bought the product sees a note that only purchasers can review it.

Below that, every other review is listed newest first, each showing the reviewer's first name and last initial, a "Verified purchase" badge, the stars, the comment, and the date — with "(edited)" when the author has changed it and "Edited by staff" when a moderator has.

Staff moderate right on the product page: every review shows them Edit and Delete. A staff edit can change a review's comment (for example, to remove abusive language) but never its stars, and marks the review "Edited by staff." Reviews are also listed in the Django admin as a store-wide safety net.

Every create, edit, cancel, and delete redraws the Reviews section in place, without reloading the page.

## User Stories

**Visitor (not signed in)**

1. As a visitor, I want to see a product's reviews and rating summary on its detail page, so that I can learn what buyers think before I sign in or buy.
2. As a visitor, I want the "Your review" area to tell me to sign in to review, so that I know reviewing is possible.
3. As a visitor, I want the sign-in link to bring me back to the same product, so that I don't have to hunt for it again.

**Shopper (anyone viewing a product)**

4. As a shopper, I want to see the product's average star rating and number of reviews at the top of the reviews section, so that I get the overall verdict at a glance.
5. As a shopper, I want a product with no reviews to say "No reviews yet — be the first," so that the section isn't confusingly blank.
6. As a shopper, I want to see every review for a product, newest first, so that the most recent opinions are on top.
7. As a shopper, I want each review to show its stars, its comment (if any), and the date it was posted, so that I can judge it.
8. As a shopper, I want each review to show the reviewer as first name and last initial (or their username if no name is set), so that reviews feel human without exposing anyone's full name.
9. As a shopper, I want every review to carry a "Verified purchase" badge, so that I know it comes from someone who bought the product.
10. As a shopper, I want a review the author has changed to say "(edited)," so that I know it may differ from what others read earlier.
11. As a shopper, I want a review a staff member has changed to say "Edited by staff," so that I know the store moderated its text.

**Customer (signed in)**

12. As a customer who hasn't bought a product, I want the "Your review" area to tell me only purchasers can review it, so that I understand why there's no form.
13. As a customer who has an order for a product that isn't cancelled (placed, shipped, or delivered), I want to be able to review it, so that I can share my opinion as soon as I've bought it.
14. As a customer, I want to review a product I bought even if the store has since marked it unavailable, so that my experience still counts.
15. As a customer, I want my review to be a 1-to-5 star rating with an optional written comment, so that I can leave a quick rating or a detailed one.
16. As a customer, I want the form to tell me clearly if I forgot to choose a rating or my comment is too long, so that I can fix it without losing what I typed.
17. As a customer, I want to post my review without the page reloading, so that I don't lose my place.
18. As a customer, I want my own review pinned in a "Your review" box at the top of the section, so that I can always find it.
19. As a customer, I want only one review per product, so that each buyer gets one voice.
20. As a customer who double-submits or has the page open in two tabs, I want the store to still keep just one review from me, so that I never end up with duplicates.
21. As a customer, I want to edit my review's stars and comment in place, pre-filled with what I wrote, so that I can fix a typo or change my mind without retyping everything.
22. As a customer, I want a Cancel button while editing, so that I can back out without changing anything.
23. As a customer, I want my edit to clear any "Edited by staff" marker, so that the review is shown as mine again once I've rewritten it.
24. As a customer, I want my review to stay mine even if the order I bought it in is later cancelled, so that it isn't silently taken away.
25. As a customer, I want to be asked "Delete this review?" before it's deleted, so that a slipped click doesn't lose my writing.
26. As a customer, I want my deleted review to disappear and the empty form to return in place, so that I can write a new one if I want.
27. As a customer, I want the rating summary to update immediately when I post, edit, or delete my review, so that it always matches what's shown.
28. As a customer, I want no way to edit or delete anyone else's review, so that other customers' opinions are protected, as mine are.

**Employee (staff)**

29. As an employee, I want to review products I've bought under the same rules as customers, so that I can use the store like any shopper.
30. As an employee, I want Edit and Delete buttons on every review when I view a product, so that I can moderate without leaving the page.
31. As an employee editing someone else's review, I want to change only its comment, never its stars, so that the store can clean up abusive text without ever changing a customer's rating.
32. As an employee, I want my edits to someone else's review to mark it "Edited by staff," so that moderation is transparent to shoppers and the author.
33. As an employee editing my own review, I want the normal full form, so that I'm treated as its author.
34. As an employee, I want deleting any review to ask for confirmation first, so that I don't wrongly remove a customer's review.
35. As an employee, I want to edit and delete reviews in place without reloading, so that I keep my place on long review lists.

**Admin (superuser)**

36. As the admin, I want reviews listed in the Django admin, so that I can find and remove abusive reviews across the whole store in one place.

**Developer / demo**

37. As someone demoing the store, I want the seed to create a realistic spread of reviews — mixed ratings, some with comments and some without, one marked "Edited by staff" — so that every display state can be shown without setup.
38. As someone demoing the store, I want the seeded demo customer to have already reviewed one purchased product and to have another purchased product not yet reviewed, so that I can show both the "Your review" box and the empty form.
39. As a developer, I want every seeded review backed by a real non-cancelled order, so that the seed obeys the feature's own purchase rule.
40. As a developer, I want reseeding to reset reviews along with everything else, so that the seed stays idempotent.
41. As a developer, I want deleting a product or a user to delete their reviews, so that no orphaned reviews remain.

## Implementation Decisions

**A new app**

- The feature lives in a new, self-contained `reviews` app with its own models, views, forms, URL namespace, templates, and tests. It depends on `products`, on the user model, and on one read-only query in `orders`; nothing in other apps depends on it beyond the product detail page including its section.

**Models**

- `Review` — belongs to a user and a product (deleting either deletes the review), with a rating, an optional comment, a created timestamp, an updated timestamp, and an "edited by staff" flag.
  - Rating is a small positive integer with a database check constraint keeping it between 1 and 5.
  - Comment is optional (blank allowed) with a maximum length of about 2,000 characters.
  - A database uniqueness constraint on the user–product pair guarantees one review per customer per product.
  - Default ordering is newest first.
- Model methods own the logic, keeping views thin:
  - **can_review(user, product)** (class-level) — true when the user is signed in, has purchased the product, and hasn't already reviewed it.
  - **author_edit(rating, comment)** — updates both fields and clears the staff flag.
  - **staff_edit(comment)** — updates only the comment and sets the staff flag. Never touches the rating.
  - **was_edited** — whether the review was changed after posting (updated meaningfully later than created), driving the "(edited)" marker.
  - **can_change(user)** — whether a user may edit or delete this review: its author, or any staff member.
  - **display name** of the reviewer — first name plus last initial, falling back to the username when the name is blank.
- A product-level rating summary (average to one decimal, plus count) comes from a queryset aggregation, not a stored field.

**The purchase rule**

- "Purchased" means the user has an order line for the product on an order whose status is not cancelled (placed, shipped, or delivered all count).
- This lives in `orders` as a queryset method on order items (e.g. "purchased by user for product"), because orders owns the definition of a purchase. `reviews` calls it; `orders` knows nothing about reviews.
- The rule is checked only when a review is **created**. Later cancelling the order does not hide, lock, or delete the review; abuse is handled by staff deleting it.
- No service module: creating a review is one read-only check plus one save, not a multi-step workflow. The architecture doc's "exactly two deep modules" stays accurate.
- The template uses the same rule to choose what the "Your review" box shows, but the server enforces it on every create request regardless of what was displayed.

**Permissions**

- Create: signed-in and purchased and not already reviewed. Staff follow the same purchase rule for their own reviews.
- Author edit: the review's author — rating and comment.
- Staff edit of another user's review: comment only, via a staff form that excludes the rating; sets "edited by staff."
- Staff editing their own review use the author form and are treated as the author.
- Delete: the author or any staff member.
- Requests by anyone else are rejected (403 for a signed-in user lacking permission, a redirect to sign in for anonymous users). No role field and no Groups — staff is `is_staff`.

**Forms**

- An author review form with rating and comment; rating required, comment optional, length limit enforced.
- A staff moderation form with comment only.
- Forms own their validation. An invalid submission re-renders the section with errors and the user's input preserved.

**URLs and views**

- All write endpoints are POST-only and require sign-in; the edit-form endpoint is GET.
- Create — POST by product. Rejects non-purchasers and duplicates. A duplicate caused by a double-submit or a stale tab must not error to the user; the response simply shows the existing review.
- Edit form — GET by review. Returns the section with that review's card (or the pinned box, for the author) swapped to an in-place, pre-filled form — the author form or the staff form as appropriate.
- Save edit — POST by review. Applies the author or staff edit as appropriate.
- Delete — POST by review.
- Cancel edit — re-renders the section (reuses the section view; no separate endpoint is required).
- A nonexistent product or review is a 404.
- Every response re-renders the whole Reviews section partial for that product.

**HTMX interactions**

- The whole Reviews section — summary, "Your review" box, and list — is one partial and one swap target. Every create, edit-form, save, cancel, and delete response replaces it in place. This keeps the summary always correct and handles the form ↔ posted review ↔ empty form transitions without special cases.
- Delete buttons carry an HTMX confirmation ("Delete this review?") using the browser's dialog — no custom JavaScript.
- For anonymous visitors, the "Your review" box is a plain sign-in link carrying a `next` back to the product page — no HTMX — mirroring the wishlist and add-to-cart buttons.
- No out-of-band swaps.
- Partials follow the project's convention: underscore-prefixed, under the app's partials folder, never extending the base template. CSRF is already supplied to HTMX by the base template.

**Templates**

- Product detail page: include the Reviews section below the product information. The catalog grid is unchanged.
- Section layout, top to bottom: rating summary (or the "No reviews yet — be the first" empty state); the pinned "Your review" box; the list of all other reviews, newest first, with no pagination.
- "Your review" box states: empty form (eligible, not yet reviewed); the customer's posted review with Edit and Delete; the in-place edit form; "Sign in to review this product" (anonymous); "Only customers who've purchased this product can review it" (signed in, not purchased).
- Each review card: reviewer display name, "Verified purchase" badge, stars, comment if present, posted date, "(edited)" and "Edited by staff" markers when applicable, and Edit/Delete only for users allowed to change it.
- Stars render with DaisyUI's rating component (radio inputs for the form, read-only for display) through a reusable star partial. Tailwind + DaisyUI only, Times New Roman per the template conventions.

**Admin**

- `Review` is registered in the Django admin, listing reviewer, product, rating, dates, and the staff flag, so the superuser has a store-wide view.

**Seed**

- The seed wipes reviews along with the other demo data and creates a realistic spread: several seeded users reviewing several products, mixed 1–5 ratings, some with comments and some without, one marked "Edited by staff."
- Every seeded review is backed by a real non-cancelled order for that user and product.
- The demo `customer` has reviewed one purchased product and has at least one other purchased product they haven't reviewed.

**Testing**

- pytest + pytest-django in the app's tests module, using the shared plain fixtures (`customer`, `staff_user`, `product`, …); any new shared fixture (e.g. a purchased product or a review) goes in the project-level conftest.
- Cover: the purchase query (non-cancelled orders count, cancelled orders and no orders don't, other users' orders don't); can_review; one review per user–product (constraint and view); rating range constraint and form validation; comment optional and length-limited; author_edit clears the staff flag; staff_edit changes only the comment and sets the flag; was_edited; display name and its fallback; summary average and count, including no reviews; cancelling an order after reviewing leaves the review editable; non-purchasers can't create; anonymous requests redirect to sign-in; write endpoints are POST-only; 404s on missing product or review; customers can't edit or delete others' reviews; staff can edit (comment only) and delete any review; staff editing their own review get the full form; each "Your review" box state renders correctly; markers render when applicable; delete buttons carry the confirmation; product and user deletion cascade; Review is in the admin; seed creates the demo reviews, each backed by a purchase, and reseeding is idempotent.
- The suite must be green at every phase boundary.

## Out of Scope

- Star ratings or summaries on catalog grid cards (the star partial is reusable, so this is a later addition).
- Sorting or filtering the catalog by rating.
- A styled back-office "Reviews" tab.
- Pagination or "Show more" for long review lists.
- Hiding, locking, or deleting reviews automatically when the underlying order is cancelled.
- Moderation history, audit logs, or recording which staff member edited a review.
- Staff changing a customer's star rating.
- Helpful/unhelpful votes, replies, review photos, or reporting/flagging reviews.
- Half-star or non-1-to-5 rating scales.
- Showing the reviewer's full name, or anonymous reviews.
- Review notifications or emails.
- Review analytics on the staff dashboard.

## Further Notes

- The comment is deliberately optional, a conscious change from the original request ("each review is a written comment and a rating"), to make leaving a rating quicker.
- The design mirrors the wishlist and cart (HTMX partials redrawn in place, ownership through the signed-in user, plain sign-in link for anonymous visitors) so the codebase stays predictable. Unlike the wishlist, reviews are public and are registered in the admin, because staff must be able to moderate them.
- Limiting staff to the comment is what keeps ratings trustworthy: the store can remove abusive words, or a whole review, but can never change what a customer scored.
- Remember to append this feature's AI-usage entries to `PROMPTS.md`, per the project rules.
