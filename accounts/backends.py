from django.contrib.auth import get_user_model
from django.contrib.auth.backends import ModelBackend


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
        user = self._find_user(username)
        if user is None:
            # Run the hasher anyway so a missing account takes as long to
            # reject as a wrong password (mirrors ModelBackend).
            User().set_password(password)
            return None
        if user.check_password(password) and self.user_can_authenticate(user):
            return user
        return None

    def _find_user(self, identifier):
        User = get_user_model()
        try:
            return User._default_manager.get_by_natural_key(identifier)
        except User.DoesNotExist:
            # The case-insensitive unique constraint means at most one match.
            return User._default_manager.filter(email__iexact=identifier).first()
