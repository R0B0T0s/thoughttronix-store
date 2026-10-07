# Plan: The ThoughtTronix Store — Account Security

> Source PRD: `prd/account-security.md`. The PRD owns the requirements; this
> plan owns the sequence. Where the two disagree, the PRD wins.

## Architectural decisions

Durable decisions that apply across all phases:

- **Owning app**: `accounts` owns everything user-facing here — signup, sign-in,
  the Account page, change email/password, password reset, and the security
  alert emails. Settings-level hardening lives in `config/`.
- **URLs** (all under `/accounts/`, namespace `accounts`):
  - `accounts/` → `accounts:account` — the Account page
  - `accounts/email/` → `accounts:email_change`
  - `accounts/password/` → `accounts:password_change` (on success, redirects to
    the Account page with a flash message)
  - `accounts/password-reset/` → `accounts:password_reset`
  - `accounts/password-reset/sent/` → `accounts:password_reset_done`
  - `accounts/reset/<uidb64>/<token>/` → `accounts:password_reset_confirm`
  - `accounts/reset/complete/` → `accounts:password_reset_complete`
  - Django's built-in auth views default to un-namespaced URL names, so each
    one mounted here sets its `success_url` (and the reset email template)
    against the `accounts:` names.
  - The admin moves from `admin/` to a path read from `ADMIN_URL` in `.env`,
    defaulting to something other than `admin/`.
- **Models**: there are no new store models. `User.email` gains a database
  `UniqueConstraint` on `Lower("email")` that applies only where the email
  isn't blank. Legacy blank-email accounts stay valid, and no data migration
  runs. django-axes brings its own models (attempts, lockouts, logs) through
  its own migrations.
- **Email normalization**: emails are normalized with Django's
  `normalize_email` (which lowercases the domain) wherever they are saved, and
  compared case-insensitively (`iexact`) wherever they are looked up — signup,
  email change, sign-in, and reset.
- **Authentication**: `AUTHENTICATION_BACKENDS` is the axes backend first,
  followed by an accounts-app username-or-email backend that otherwise behaves
  like `ModelBackend`. Roles are unchanged: customers are plain users,
  employees are `is_staff`, and the admin is `is_superuser`.
- **Alert emails**: a small service module in `accounts` owns the "password
  changed" and "email changed" notifications. Views call it after a
  successful change, and it skips users with no email on file. All mail —
  alerts and reset — is plain text rendered from templates.
- **Settings**: everything comes from `.env` via environs with working defaults.
  With no `.env`, the site runs exactly as it does today (debug on, the dev
  secret key, the console email backend).
- **Testing**: flows are verified through Django's test outbox
  (`mail.outbox`). Axes is disabled for the ordinary suite through a
  project-level autouse fixture, and the lockout tests turn it back on.

---

## Phase 1: Email at signup, unique regardless of capitalization

**User stories**: 1, 2, 18

### What to build

Signup asks for a required email alongside the username and password. The
form normalizes the email and rejects one already in use — including a
differently-capitalized match — with a friendly field error before the
database is ever asked. A migration adds the conditional case-insensitive
unique constraint as a backstop. Because the user now has an email, the
existing similarity validator also checks the new password against it. The
seed command keeps giving every demo user a distinct email, so it still
satisfies the constraint.

### Acceptance criteria

- [x] The signup page shows a required email field, and submitting without one fails with a form error.
- [x] Signing up with an email already in use fails with a friendly error, including when only the capitalization differs (`Ada@Example.com` vs `ada@example.com`).
- [x] A successful signup stores a normalized email on the new user.
- [x] Two existing users with blank emails can coexist (the constraint ignores blanks).
- [x] A password too similar to the email is rejected at signup.
- [x] `seed` runs twice cleanly against the new constraint.
- [x] The suite is green and Ruff is clean.

---

## Phase 2: Sign in with username or email

**User stories**: 3

### What to build

A username-or-email authentication backend in `accounts` replaces the stock
model backend. It finds the user by exact username or by case-insensitive
email, checks the password the same way Django does, and rejects inactive
users. The sign-in field's label says it accepts either one.

### Acceptance criteria

- [x] A customer can sign in with their username.
- [x] A customer can sign in with their email, in any capitalization.
- [x] A wrong password fails for both username and email.
- [x] An inactive user cannot sign in by either route.
- [x] A user with a blank email can still sign in by username, and a blank identifier never matches a blank-email account.
- [x] The sign-in label reads "Username or email" (or equivalent).

---

## Phase 3: Account page and change email, with an alert to the old address

**User stories**: 9, 10, 11, 12, 13, 14

### What to build

A login-required Account page at `accounts:account` shows the signed-in
user's current email, or a prompt to add one if it's blank, and links to
change it. The navbar gains an "Account" link next to "Addresses". The
change-email form requires the current password plus the new email and checks
uniqueness the same way signup does. The accounts alert-email service is born
here: after a successful change it sends a plain-text "your email was
changed" notice to the *old* address. Nothing is sent if there was no old
address.

### Acceptance criteria

- [x] Anonymous visitors are redirected to sign in from the Account and change-email pages.
- [x] The Account page shows the current email, or an "add an email" prompt when it's blank.
- [x] The navbar shows "Account" next to "Addresses" for signed-in users.
- [x] A wrong current password rejects the change and leaves the email untouched.
- [x] An email already used by another account (in any capitalization) is rejected.
- [x] A successful change saves the normalized new email, flashes a message, and sends exactly one alert, addressed to the old email.
- [x] Adding an email to a blank-email account succeeds and sends no alert.

---

## Phase 4: Change password, with an alert

**User stories**: 15, 16, 17, 18

### What to build

The Account page links to `accounts:password_change`, which uses Django's
built-in password change view and form, styled to match the site. The user
enters their current password and the new one twice. Django's built-in
behavior keeps this session signed in and invalidates the user's other
sessions. On success the user returns to the Account page with a flash
message, and the alert service sends a "your password was changed" notice to
the account's email (or nothing if there is none). New passwords run through
the existing four validators.

### Acceptance criteria

- [x] The page requires login and renders in the site's style.
- [x] A wrong current password, mismatched new passwords, or a validator failure each rejects the change.
- [x] A successful change lets the user sign in with the new password and not the old one.
- [x] The session that made the change stays signed in, and a second session for the same user is signed out.
- [x] Exactly one alert email goes to the account's email, and none goes out when the email is blank.

---

## Phase 5: Password reset by email

**User stories**: 4, 5, 6, 7, 8

### What to build

The sign-in page gains a "Forgot your password?" link. Django's four built-in
reset views are mounted under the `accounts` namespace and styled with site
templates: request, sent, confirm, and complete. The reset email is plain
text and links to the namespaced confirm URL. `PASSWORD_RESET_TIMEOUT` is one
hour, and links are single-use by Django's token design. Registered and
unregistered emails get the identical "check your inbox" response. An
expired or already-used link shows a clear "this link is no longer valid —
request a new one" message with a link back to the request form.

### Acceptance criteria

- [x] The sign-in page links to the reset request page.
- [x] Requesting a reset for a registered email (in any capitalization) sends one email whose link opens the set-new-password form.
- [x] Requesting a reset for an unknown email sends nothing and returns the same response as a registered one.
- [x] Setting a new password through a valid link lets the user sign in with it.
- [x] Reusing a link after it has been used shows the invalid-link message.
- [x] A link older than one hour shows the invalid-link message.
- [x] Users with a blank email cannot be reset by email.

---

## Phase 6: Per-email reset cooldown

**User stories**: 20

### What to build

The reset request form is customized so each address receives at most one
reset email every five minutes, tracked in Django's cache by normalized
address. A throttled request returns the same confirmation page as any other
request, so the throttle reveals nothing about whether the account exists.

### Acceptance criteria

- [x] A second request for the same address within five minutes sends no email but shows the normal confirmation.
- [x] Differently-capitalized requests for the same address share one cooldown.
- [x] Once the cooldown has passed, a new request sends an email again.
- [x] Cooldowns for different addresses are independent.
- [x] The cache is cleared between tests so cooldowns don't leak.

---

## Phase 7: Login lockout with django-axes

**User stories**: 19, 21

### What to build

Add django-axes. It locks out a username + IP combination after five failed
sign-ins, for a cool-off period. Its backend sits ahead of the
username-or-email backend, and its middleware is installed. A locked-out
attempt sees a styled lockout message rather than a bare error. Staff can
view and clear lockouts in the Django admin. An autouse test fixture disables
axes for the ordinary suite, and the lockout tests re-enable it.

### Acceptance criteria

- [x] After five wrong passwords for one username from one IP, the next sign-in is refused, even with the correct password.
- [x] A different username from the same IP is not locked out.
- [x] Clearing the lockout (as the admin action would) lets the user sign in again.
- [x] Lockout records appear in the Django admin for staff.
- [x] The rest of the suite (signup, sign-in, change password, reset) is unaffected and green.

---

## Phase 8: Real email delivery from the environment

**User stories**: 23, 24

### What to build

The console backend stays the default. When mail-server values are present
in `.env` (host, port, user, password, TLS, and a default "from" address),
settings switch to the SMTP backend. Credentials live only in `.env`.
`.env.example` documents the new keys, commented out, and the alert and reset
emails come from the configured "from" address.

### Acceptance criteria

- [x] With no mail settings, emails print to the terminal.
- [x] With an email host set, `EMAIL_BACKEND` is the SMTP backend and the host, port, user, password, and TLS values come from `.env`.
- [x] `DEFAULT_FROM_EMAIL` comes from `.env` with a sensible store default.
- [x] `.env.example` lists every mail key, and no credentials appear in source.

---

## Phase 9: Production hardening and a configurable admin URL

**User stories**: 22, 25, 26, 27

### What to build

Local defaults stay as they are. When `DEBUG` is off, settings refuse to load
if the secret key is still the development default, raising a clear
`ImproperlyConfigured`. Debug-off also turns on secure session and CSRF
cookies, the HTTPS redirect, and HSTS. The admin mounts at the path read from
`ADMIN_URL`, which defaults to something other than `admin/`. Run
`check --deploy` with debug off and a strong secret key and resolve every
warning. Update `docs/ARCHITECTURE.md` (Settings) and `CLAUDE.md` where the
new environment keys or the admin path change what a developer needs to know,
and append the build's entry to `PROMPTS.md`.

### Acceptance criteria

- [ ] With no `.env`, the site runs in debug mode with the dev secret key, as it does today.
- [ ] Loading settings with `DEBUG=false` and the default secret key fails with a clear error (tested in a subprocess).
- [ ] With `DEBUG=false` and a proper key, secure cookies, the SSL redirect, and HSTS are all enabled.
- [ ] `manage.py check --deploy` passes with no warnings under that configuration.
- [ ] `/admin/` returns 404, and the admin is reachable at the configured path.
- [ ] Docs reflect the new settings, and `PROMPTS.md` has a new entry appended.
