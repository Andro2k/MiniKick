# tests\test_command_parser.py

from frontend.common.utils import validate_trigger_prefix

def test_validate_trigger_prefix_valid():
    assert validate_trigger_prefix("!tts") is True
    assert validate_trigger_prefix("!sr") is True
    assert validate_trigger_prefix("!skip") is True
    assert validate_trigger_prefix("") is True

def test_validate_trigger_prefix_invalid():
    assert validate_trigger_prefix("tts") is False
    assert validate_trigger_prefix("sr") is False
