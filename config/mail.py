"""A console email backend that prints messages as a reader would see them.

Django's stock console backend prints the raw MIME message. Any body line
longer than 78 characters — a password reset link, say — makes Python
encode the body as quoted-printable, which wraps the link with a stray
``=`` and mangles its token, so a link copied from the terminal is broken.
This backend prints the headers followed by the *decoded* text, so links
come out whole and copyable. Real mail clients decode the encoding
themselves; this is for development only.
"""

from django.core.mail.backends.console import EmailBackend as ConsoleEmailBackend

# Transport details that mean nothing once the body is decoded.
_SKIPPED_HEADERS = {"content-transfer-encoding", "mime-version"}


class ReadableConsoleEmailBackend(ConsoleEmailBackend):
    def write_message(self, message):
        msg = message.message()
        for name, value in msg.items():
            if name.lower() not in _SKIPPED_HEADERS:
                self.stream.write(f"{name}: {value}\n")
        self.stream.write("\n")
        for part in msg.walk():
            if part.get_content_type() == "text/plain":
                payload = part.get_payload(decode=True)
                self.stream.write(payload.decode(part.get_content_charset("utf-8")))
                self.stream.write("\n")
        self.stream.write("-" * 79)
        self.stream.write("\n")
