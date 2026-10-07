"""Security alert emails.

When sign-in details change, the account's owner hears about it — so a
hijacker can't quietly take over. Views call these after a successful
change; accounts with no email on file simply get no alert. All alerts
are plain text rendered from templates.
"""

from django.contrib.auth.models import AbstractBaseUser
from django.core.mail import send_mail
from django.template.loader import render_to_string


def _send_alert(to: str, subject: str, template: str, context: dict) -> None:
    if not to:
        return
    body = render_to_string(template, context)
    send_mail(subject, body, from_email=None, recipient_list=[to])


def notify_email_changed(user: AbstractBaseUser, old_email: str) -> None:
    """Tell the *old* address that the account's email was changed."""
    _send_alert(
        old_email,
        "Your ThoughtTronix email was changed",
        "accounts/emails/email_changed.txt",
        {"user": user, "old_email": old_email, "new_email": user.email},
    )
