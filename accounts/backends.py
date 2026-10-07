from django.contrib.auth import get_user_model
from django.contrib.auth.backends import ModelBackend


def find_user(identifier):
    """The user a sign-in identifier names: an exact username match wins,
    otherwise a case-insensitive email match. ``None`` if neither.
    """
    if not identifier:
        # A blank identifier must never match a blank-email account.
        return None
    User = get_user_model()
    try:
        return User._default_manager.get_by_natural_key(identifier)
    except User.DoesNotExist:
        # The case-insensitive unique constraint means at most one match.
        return User._default_manager.filter(email__iexact=identifier).first()


def lockout_username(request, credentials=None):
    """The username django-axes counts failed sign-ins against.

    An identifier that names an account resolves to that account's
    username, so "ada", "ada@example.com" and "ADA@EXAMPLE.COM" share one
    failure count — an attacker can't dodge the lockout by switching
    between them. Unknown identifiers are counted as typed, lowercased.
    """
    if credentials:
        identifier = credentials.get("username")
    else:
        identifier = request.POST.get("username")
    user = find_user(identifier)
    if user is not None:
        return user.username
    return (identifier or "").lower()


class UsernameOrEmailBackend(ModelBackend):
    """``ModelBackend`` that also accepts an email in the username field.

    An exact username match wins; otherwise the identifier is compared to
    emails case-insensitively. Everything else — password checking,
    rejecting inactive users, permissions — is the stock backend's.
    """

    def authenticate(self, request, username=None, password=None, **kwargs):
        User = get_user_model()
        if username is None:
            username = kwargs.get(User.USERNAME_FIELD)
        if not username or password is None:
            return None
        user = find_user(username)
        if user is None:
            # Run the hasher anyway so a missing account takes as long to
            # reject as a wrong password (mirrors ModelBackend).
            User().set_password(password)
            return None
        if user.check_password(password) and self.user_can_authenticate(user):
            return user
        return None
