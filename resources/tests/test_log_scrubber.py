# resources\tests\test_log_scrubber.py

import io
import logging

import pytest

from backend.utils import SecretRedactingFilter, redact_secrets

TOKEN = "SECRET-token_abc"


@pytest.mark.parametrize("url", [
    f"https://discord.com/api/webhooks/123456/{TOKEN}",
    f"https://discordapp.com/api/webhooks/123456/{TOKEN}",
    f"https://canary.discord.com/api/webhooks/123456/{TOKEN}",
    f"https://ptb.discord.com/api/v10/webhooks/123456/{TOKEN}",
    f"discord.com/api/webhooks/123456/{TOKEN}",
    f"https://discord.com/api/webhooks/123456/{TOKEN}/messages/99?wait=true",
])
def test_discord_webhook_tokens_are_masked(url):
    redacted = redact_secrets(f"POST failed for {url} (timeout)")
    assert TOKEN not in redacted
    assert "[REDACTED]" in redacted and "123456" in redacted


def test_unrelated_text_is_untouched_and_redaction_is_idempotent():
    plain = "Connected to https://api.kick.com/public/v1/chat"
    assert redact_secrets(plain) == plain
    once = redact_secrets(f"https://discord.com/api/webhooks/1/{TOKEN}")
    assert redact_secrets(once) == once


def _logger_with_filter():
    stream = io.StringIO()
    handler = logging.StreamHandler(stream)
    handler.setFormatter(logging.Formatter("%(message)s"))
    handler.addFilter(SecretRedactingFilter())
    logger = logging.getLogger("test.log_scrubber")
    logger.handlers = [handler]
    logger.setLevel(logging.DEBUG)
    logger.propagate = False
    return logger, stream


def test_filter_masks_lazy_format_arguments():
    logger, stream = _logger_with_filter()
    logger.error("delivery failed: %s", f"https://discord.com/api/webhooks/1/{TOKEN}")
    assert TOKEN not in stream.getvalue()


def test_filter_masks_tokens_inside_tracebacks():
    logger, stream = _logger_with_filter()
    try:
        raise RuntimeError(f"boom https://discord.com/api/webhooks/1/{TOKEN}")
    except RuntimeError:
        logger.exception("unexpected")
    output = stream.getvalue()
    assert "Traceback" in output and TOKEN not in output
