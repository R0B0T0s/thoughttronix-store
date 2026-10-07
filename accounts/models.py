from django.conf import settings
from django.contrib.auth.models import AbstractUser, UserManager
from django.db import models
from django.db.models.functions import Lower


class StoreUserManager(UserManager):
    def email_in_use(self, email, exclude=None):
        """True if another account already has ``email``, in any capitalization.

        Blank emails never count as in use. Pass ``exclude`` (a user) to
        ignore that account — e.g. the one changing its own email.
        """
        if not email:
            return False
        matches = self.filter(email__iexact=email)
        if exclude is not None:
            matches = matches.exclude(pk=exclude.pk)
        return matches.exists()


class User(AbstractUser):
    """The store's user model.

    Roles use Django's own vocabulary and nothing else: customers are
    plain users, employees are ``is_staff``, the admin is ``is_superuser``.
    """

    objects = StoreUserManager()

    # Nullable per the PRD: an absent job title is unknown, not empty.
    job_title = models.CharField(max_length=150, null=True, blank=True)  # noqa: DJ001

    class Meta(AbstractUser.Meta):
        constraints = [
            # One account per email, whatever the capitalization. Blank
            # emails are exempt so accounts that predate the requirement
            # stay valid. Forms check this first with a friendlier
            # message; the constraint is the backstop.
            models.UniqueConstraint(
                Lower("email"),
                condition=~models.Q(email=""),
                name="unique_user_email_ci",
                violation_error_message="An account with that email already exists.",
            ),
        ]


class Address(models.Model):
    """A saved address on a customer's account, reusable at checkout.

    Kind-agnostic by design: an address isn't inherently "for shipping"
    or "for billing" — either default flag can be set independently, so
    the same address can back both, or two different addresses can.
    Saving here never touches ``Order``, which keeps its own flat,
    denormalized address fields untouched by later edits or deletions.
    """

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="addresses",
    )
    label = models.CharField(max_length=50)
    recipient_name = models.CharField(max_length=100)
    street = models.CharField(max_length=200)
    line2 = models.CharField(max_length=200, blank=True)
    city = models.CharField(max_length=100)
    state = models.CharField(max_length=2)
    zip_code = models.CharField(max_length=10)
    is_default_shipping = models.BooleanField(default=False)
    is_default_billing = models.BooleanField(default=False)

    class Meta:
        ordering = ["label"]

    def __str__(self):
        return f"{self.label} ({self.user})"

    def make_default_shipping(self):
        """Mark this the default shipping address, unsetting any other."""
        Address.objects.filter(user=self.user, is_default_shipping=True).exclude(
            pk=self.pk
        ).update(is_default_shipping=False)
        self.is_default_shipping = True
        self.save(update_fields=["is_default_shipping"])

    def make_default_billing(self):
        """Mark this the default billing address, unsetting any other."""
        Address.objects.filter(user=self.user, is_default_billing=True).exclude(
            pk=self.pk
        ).update(is_default_billing=False)
        self.is_default_billing = True
        self.save(update_fields=["is_default_billing"])
