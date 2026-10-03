## Template conventions

- Every page extends the project-level `templates/base.html` (DaisyUI navbar,
  footer motto). DaisyUI theme: `night`, set in `assets/css/source.css` and
  `data-theme` on `<html>`.
- Back-office pages extend `templates/backoffice/base.html` — the staff shell
  with the tab rail; the active tab comes from the view's `section` context
  entry.
- HTMX endpoints render partials from `templates/<app>/partials/_<name>.html` —
  prefixed with an underscore, never extending `base.html`.
- Every list view gets a designed empty state, not a blank page.
- Styling is Tailwind + DaisyUI classes only; no crispy-forms, no JavaScript
  beyond HTMX. One sanctioned exception: product images render through
  `products/partials/_image.html`, whose `onerror` swaps in the placeholder
  if the browser can't load the file.

-Styling utilizes Times New Roman font.