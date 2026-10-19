# resources\tests\test_tray_and_slider_debouncing.py

import pytest
from PySide6.QtWidgets import QApplication
from unittest.mock import MagicMock
from frontend.navigation.tray_menu_component import SystemTrayManager
from frontend.components.music.music_settings_panel import MusicSettingsPanel


class MockI18n:
    def get(self, key, **kwargs):
        translations = {
            "main.tray.open_panel": "Abrir Panel",
            "main.tray.play": "Reproducir Música",
            "main.tray.pause": "Pausar Música",
            "main.tray.skip": "Saltar Canción",
            "main.tray.read_chat": "Leer chat",
            "main.tray.tts_use_command": "Requerir comando",
            "main.tray.tts_voice_type": "Voces Web",
            "main.tray.close_app": "Cerrar MiniKick",
            "main.tray.tooltip": f"MiniKick v{kwargs.get('version', '1.6.0')} | Activo",
            "music.tabs.settings": "Ajustes de Música",
            "music.youtube.auto_resume_title": "Auto-reanudar",
            "music.youtube.auto_resume_desc": "Desc auto-reanudar",
            "music.youtube.media_keys_title": "Teclas multimedia",
            "music.youtube.media_keys_desc": "Desc teclas multimedia",
            "music.youtube.max_user_songs_title": "Máx canciones",
            "music.youtube.max_user_songs_desc": "Desc canciones",
            "music.youtube.user_cooldown_title": "Cooldown usuario",
            "music.youtube.user_cooldown_desc": "Desc cooldown",
            "music.youtube.max_queue_size_title": "Cola máx",
            "music.youtube.max_queue_size_desc": "Desc cola",
            "music.youtube.max_song_duration_title": "Duración máx",
            "music.youtube.max_song_duration_desc": "Desc duración",
        }
        return translations.get(key, key)

@pytest.fixture
def app():
    instance = QApplication.instance()
    if not instance:
        instance = QApplication([])
    return instance

def test_system_tray_manager_playback_toggle_and_tooltip(app):
    i18n = MockI18n()
    tray = SystemTrayManager(i18n)

    assert tray.toolTip() == "MiniKick v1.6.0 | Activo"
    assert tray.action_play_pause.text() == "Reproducir Música"
    assert not tray.action_play_pause.icon().isNull()
    assert not tray.action_restore.icon().isNull()
    assert not tray.action_skip.icon().isNull()
    assert not tray.action_quit.icon().isNull()

    tray.set_playback_state(True)
    assert tray.action_play_pause.text() == "Pausar Música"
    assert not tray.action_play_pause.icon().isNull()

    tray.set_playback_state(False)
    assert tray.action_play_pause.text() == "Reproducir Música"

def test_music_settings_panel_slider_debouncing(app):
    i18n = MockI18n()
    panel = MusicSettingsPanel(i18n)

    mock_max_songs_slot = MagicMock()
    panel.max_user_songs_changed.connect(mock_max_songs_slot)

    panel.slider_max_user_songs.setValue(3)
    panel.slider_max_user_songs.setValue(4)
    panel.slider_max_user_songs.setValue(5)

    assert panel.lbl_max_user_songs.text() == "5"

    assert mock_max_songs_slot.call_count == 0

    panel._on_slider_released()

    assert mock_max_songs_slot.call_count == 1
    mock_max_songs_slot.assert_called_once_with(5)
