# backend\utils\security_utils.py

import logging
import re

REDACTED = "[REDACTED]"

_DISCORD_WEBHOOK_RE = re.compile(
    r"((?:https?://)?(?:[\w-]+\.)*discord(?:app)?\.com/api(?:/v\d+)?/webhooks/\d+/)[\w-]+",
    re.IGNORECASE,
)


def redact_secrets(text: str) -> str:
    return _DISCORD_WEBHOOK_RE.sub(rf"\1{REDACTED}", text)


class SecretRedactingFilter(logging.Filter):
    def filter(self, record: logging.LogRecord) -> bool:
        try:
            message = record.getMessage()
            redacted = redact_secrets(message)
            if redacted != message:
                record.msg = redacted
                record.args = ()
            if record.exc_info and not record.exc_text:
                record.exc_text = logging.Formatter().formatException(record.exc_info)
            if record.exc_text:
                record.exc_text = redact_secrets(record.exc_text)
        except Exception:
            return True
        return True
