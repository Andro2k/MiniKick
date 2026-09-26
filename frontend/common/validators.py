# frontend\common\validators.py

from backend.utils.command_utils import (
    sanitize_command_trigger as _backend_sanitize,
    validate_trigger_prefix as _backend_validate,
    is_complete_valid_trigger as _backend_is_complete,
)


def sanitize_command_trigger(raw_text: str) -> str:
    return _backend_sanitize(raw_text)


def validate_trigger_prefix(text: str) -> bool:
    return _backend_validate(text)


def is_complete_valid_trigger(text: str) -> bool:
    return _backend_is_complete(text)
