# frontend\common\validators.py

def validate_trigger_prefix(text: str) -> bool:
    return not text.strip() or text.startswith("!")
