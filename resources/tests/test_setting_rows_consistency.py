# resources\tests\test_setting_rows_consistency.py

import pytest
from PySide6.QtWidgets import QWidget

from backend.services.system import TranslationService
from frontend.components.chat.bot_mute import BotMutePanel
from frontend.components.music.commands_panel import MusicCommandsPanel
from frontend.components.music.music_settings_panel import MusicSettingsPanel
from frontend.components.music.player_settings import MusicPlayerSettingsPanel
from frontend.widgets import SettingRow, SliderRow
from resources.tests.test_chat_voice_rows import _icon_labels, _roles

_PANELS = {
    "music_settings": (MusicSettingsPanel, 6),
    "music_commands": (MusicCommandsPanel, 7),
    "music_player": (MusicPlayerSettingsPanel, 1),
    "chat_bot_mute": (BotMutePanel, 2),
}


def _rows(panel: QWidget) -> list[QWidget]:
    return panel.findChildren(SettingRow) + panel.findChildren(SliderRow)


@pytest.mark.parametrize("name", list(_PANELS))
def test_panel_rows_are_clean(qapp, name):
    panel_cls, expected_rows = _PANELS[name]
    panel = panel_cls(TranslationService(default_lang="es"))
    rows = _rows(panel)

    assert len(rows) == expected_rows
    for row in rows:
        roles = set(_roles(row).values())
        assert not _icon_labels(row), f"{name}: {type(row).__name__} aún muestra un ícono"
        assert {"setting_title", "caption"} <= roles
        assert "h3" not in roles
