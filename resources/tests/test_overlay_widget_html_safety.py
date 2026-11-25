# resources\tests\test_overlay_widget_html_safety.py
"""Evita que los widgets vuelvan a interpolar datos del chat dentro de innerHTML."""

import re
from pathlib import Path

_WIDGETS = Path(__file__).resolve().parents[2] / "assets" / "overlays" / "widgets"


def test_emote_combo_does_not_interpolate_chat_data_into_html():
    source = (_WIDGETS / "emote_combo.html").read_text(encoding="utf-8")
    unsafe = re.findall(r"innerHTML\s*=\s*`[^`]*\$\{(?:emoteName|emoteSrc)\}", source)
    assert unsafe == []
