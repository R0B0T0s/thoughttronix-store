# PRD: The ThoughtTronix Store — Account Security

*Commissioned by ThoughtTronix Product Management. "Your Thoughts, Our Business."*

---

## Problem Statement

Customers can create an account, but the account knows almost nothing about them. Signup asks for a username and a password and nothing else, so the store has no way to reach a customer outside the website. A customer who forgets their password has no way back in; their order history and saved addresses are simply stranded. A customer who suspects their password has leaked cannot change it — there is no page for that either.

Behind the scenes the gaps are wider. The login form accepts unlimited password guesses, so an attacker can try a dictionary of passwords against any account and nothing will stop them. The project's settings default to development values — debug mode on, a publicly known secret key, cookies allowed over plain HTTP — and nothing prevents those defaults from reaching a real server. The admin site lives at the most guessable address on the internet.

## Solution

Every new account is tied to an email address that belongs to that account alone. Customers can sign in with either their username or their email. A new **Account** page, alongside Addresses in the navbar, lets a signed-in customer change their email (after confirming their current password) and change their password. A "Forgot your password?" link on the sign-in page sends a time-limited, single-use reset link to the customer's email.

Whenever a password or email changes, the store sends an alert email so the real owner learns about it — an email change alerts the *old* address, so a hijacker cannot quietly redirect the account.

Underneath, the store defends itself: repeated failed logins lock out the attacker, repeated reset requests for the same address are throttled, and production deployments refuse to run with development-grade secrets or insecure cookie settings. Email prints to the terminal during development and is sent for real once mail-server credentials are supplied.

## User Stories

**Visitor (not signed in)**

1. As a visitor, I want to provide an email address when I sign up, so that the store can reach me if I lose access to my account.
2. As a visitor, I want signup to reject an email that is already in use — regardless of capitalization — so that each email address leads to exactly one account.
3. As a visitor, I want to sign in with either my username or my email address, so that I don't need to remember which one I used.
4. As a visitor who forgot my password, I want to request a reset link by entering my email, so that I can regain access to my account.
5. As a visitor requesting a reset, I want to see the same confirmation message whether or not my email is registered, so that strangers cannot use the form to discover who has an account.
6. As a visitor, I want the reset link to expire after one hour and stop working once used, so that an old email in my inbox cannot be used to take over my account later.
7. As a visitor following a valid reset link, I want to choose a new password and then be able to sign in with it, so that the reset actually restores my access.
8. As a visitor following an expired or already-used reset link, I want a clear message telling me to request a new one, so that I am not left confused.

**Customer (signed in)**

9. As a customer, I want an Account page reachable from the navbar, so that I have one place to manage my sign-in details.
10. As a customer, I want to see my current email on the Account page, so that I know where reset and alert emails will go.
11. As a customer whose account predates the email requirement, I want to add an email from the Account page, so that I can use password reset too.
12. As a customer, I want to change my email after confirming my current password, so that someone using my unattended session cannot redirect my account.
13. As a customer changing my email, I want the new email to be checked for uniqueness, so that I cannot collide with another account.
14. As a customer, I want an alert sent to my *old* email when my email changes, so that I find out if someone else changed it.
15. As a customer, I want to change my password by entering my current one and a new one twice, so that I can replace a password I think has leaked.
16. As a customer, I want to stay signed in on this device after changing my password while other devices are signed out, so that a leaked session elsewhere is cut off without inconveniencing me.
17. As a customer, I want an alert email when my password changes, so that I find out if someone else changed it.
18. As a customer, I want new passwords to be checked against the existing rules (minimum 8 characters, not common, not all numeric, not too similar to my username or email), so that I don't choose an easily guessed password.

**Attacker defense (customer's perspective)**

19. As a customer, I want my account to lock out a sign-in attempt after repeated wrong passwords, so that an attacker cannot guess my password by brute force.
20. As a customer, I want the store to send at most one reset email to my address every five minutes, so that nobody can flood my inbox with reset requests.

**Employee / admin (staff)**

21. As staff, I want to view and clear login lockouts in the Django admin, so that I can help a customer who locked themselves out.
22. As the admin, I want the admin site to live at a configurable, non-default address, so that automated scanners cannot find it trivially.

**Developer / deployer**

23. As a developer, I want emails to print to the terminal by default, so that I can test signup and reset flows without any mail setup.
24. As a deployer, I want to switch to real email delivery by setting mail-server values in the environment file, so that real customers receive reset links without code changes.
25. As a deployer, I want the site to refuse to start with debug off and the default secret key, so that a forgotten setting cannot ship a known secret to production.
26. As a deployer, I want secure cookies, HTTPS redirect, and HSTS enabled automatically when debug is off, so that sessions cannot be stolen over plain HTTP.
27. As a deployer, I want Django's deployment check to pass cleanly with debug off and a proper secret key, so that I can verify the configuration before going live.

## Implementation Decisions

**User model and data**

- The user model's email field becomes required at signup and unique, case-insensitively. Uniqueness is enforced by a database constraint on the lowercased email that applies only to non-blank values, so existing accounts with a blank email remain valid and no data migration rewrites anyone's records.
- Emails are normalized (lowercased domain at minimum; comparisons are case-insensitive) consistently wherever they are saved or looked up — signup, email change, login, and reset.
- The seed command already gives every demo user a distinct email; it continues to do so and must satisfy the new constraint.

**Signup**

- The signup form adds a required email field and validates case-insensitive uniqueness with a friendly form error, rather than relying on the database constraint to raise.
- There is no email verification step. Accounts are usable immediately after signup, as today.

**Sign-in**

- A small custom authentication backend lets the sign-in field accept either a username or an email. It behaves like the stock model backend otherwise (inactive users rejected, password checked the same way).
- The sign-in form's label reflects that either value is accepted. The sign-in page gains a "Forgot your password?" link.

**Account page**

- A new login-required Account page in the accounts app shows the current email and links to change email and change password. The navbar gains an "Account" link next to "Addresses".
- Change email is a form requiring the current password plus the new email; it validates uniqueness the same way signup does.
- Change password uses Django's built-in password change view and form, styled to match the site. Django's built-in behavior keeps the current session valid and invalidates the user's other sessions.

**Password reset**

- Uses Django's built-in password reset views (request, done, confirm, complete), mounted under the accounts URL namespace and styled with the site's templates.
- The reset link lifetime is one hour. Links are single-use by Django's token design.
- The reset request form is customized to apply a per-email cooldown: at most one reset email per address per five minutes, tracked in Django's cache. A throttled request shows the same confirmation message as any other request, so nothing about the account is revealed.
- Users with a blank email cannot reset by email — the built-in behavior of matching no account applies.

**Alert emails**

- A small service module in the accounts app owns the security notification emails: "your password was changed" (sent to the account's email) and "your email was changed" (sent to the *old* email). Views call the service after a successful change; logic stays out of the views.
- Accounts with no email on file simply receive no alert.
- Emails are plain-text, rendered from templates.

**Email delivery**

- The console email backend remains the default. When mail-server settings (host, port, user, password, TLS, and a default "from" address) are present in the environment file, the SMTP backend is used instead. Credentials live only in the environment file, never in source.

**Login throttling**

- The django-axes package is added. It locks out a username + IP combination after a set number of failures (around five) for a cool-off period, and exposes lockouts in the Django admin for staff to clear.
- Axes' authentication backend is placed ahead of the username-or-email backend. Test settings are configured so axes does not interfere with ordinary test logins.

**Production hardening**

- Local defaults stay convenient: with no environment file, the site runs in debug mode with the development secret key, exactly as today.
- When debug is off: the site refuses to start if the secret key is the development default; secure session and CSRF cookies, HTTPS redirect, and HSTS are enabled. The goal is a clean `check --deploy`.
- The admin URL path is read from the environment, defaulting to something other than `admin/`.

**Passwords**

- The minimum length stays at Django's default of 8. The four existing validators remain; the similarity validator now naturally also considers the email.

**Roles**

- No change to the role model: customers are plain users, employees are `is_staff`, the admin is `is_superuser`. All new account features apply to every user.

## Out of Scope

- Email verification / "confirm your address" links at signup or on email change.
- Email-only login or retiring usernames.
- Two-factor authentication, passkeys, or social login.
- Raising the minimum password length or adding complexity rules.
- Per-IP throttling of password reset requests (only the per-email cooldown is in scope).
- Editing other profile fields (first name, last name, job title) from the Account page.
- Account deletion or data export.
- HTML-formatted emails; alert and reset emails are plain text.
- Choosing or configuring a specific production mail provider or hosting platform.

## Further Notes

- Tests should exercise every flow through Django's test outbox, which captures sent email: signup with duplicate and differently-capitalized emails, login by username and by email, change email (wrong current password, duplicate, success with alert to the old address), change password (success with alert, other sessions invalidated), reset (unknown email gives the same response, cooldown suppresses a second email, expired and reused links rejected), axes lockout, and the debug-off startup guard.
- The core-platform PRD described signup as having "no email"; this PRD supersedes that decision.
- Remember to append an entry to `PROMPTS.md` when this work is built.
