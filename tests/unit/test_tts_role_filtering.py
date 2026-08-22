# tests\unit\test_tts_role_filtering.py

from backend.handlers.tts_voice_handler import TTSVoiceHandler
from backend.services.chat.chat_service import ChatService

class DummySettingsStorage:
    def __init__(self, initial=None):
        self.data = initial or {}

    def load_bool(self, key, default=False):
        return self.data.get(key, default)

    def save_bool(self, key, value):
        self.data[key] = bool(value)

    def load_string(self, key, default=""):
        return self.data.get(key, default)

    def save_string(self, key, value):
        self.data[key] = str(value)

def test_tts_voice_handler_is_role_enabled():
    handler = TTSVoiceHandler(None, None, None, None, None)
    
    settings = {
        "role_enabled_everyone": True,
        "role_enabled_broadcaster": True,
        "role_enabled_moderator": False,
        "role_enabled_vip": True,
        "role_enabled_subscriber": False
    }

    assert handler.is_role_enabled(["broadcaster"], settings) is True
    assert handler.is_role_enabled(["moderator"], settings) is False
    assert handler.is_role_enabled(["vip"], settings) is True
    assert handler.is_role_enabled(["subscriber"], settings) is False
    assert handler.is_role_enabled([], settings) is True
    assert handler.is_role_enabled(["viewer"], settings) is True

    settings["role_enabled_everyone"] = False
    assert handler.is_role_enabled([], settings) is False
    assert handler.is_role_enabled(["viewer"], settings) is False
    assert handler.is_role_enabled(["vip"], settings) is True

def test_chat_service_role_enabled_persistence():
    storage = DummySettingsStorage()
    service = ChatService(tts_manager=None, settings_storage=storage)

    service.save_settings({
        "role_enabled_everyone": False,
        "role_enabled_broadcaster": True,
        "role_enabled_moderator": False,
        "role_enabled_vip": True,
        "role_enabled_subscriber": False
    })

    loaded = service.get_settings()
    assert loaded["role_enabled_everyone"] is False
    assert loaded["role_enabled_broadcaster"] is True
    assert loaded["role_enabled_moderator"] is False
    assert loaded["role_enabled_vip"] is True
    assert loaded["role_enabled_subscriber"] is False

def test_chat_view_property_setters():
    from PySide6.QtWidgets import QApplication
    from frontend.views.chat_view import ChatView
    from backend.services.system.translation_service import TranslationService

    app = QApplication.instance() or QApplication([])
    i18n = TranslationService(default_lang="es")
    view = ChatView(i18n=i18n)
    
    view.tts_enabled = False
    assert view.tts_enabled is False
    view.tts_enabled = True
    assert view.tts_enabled is True

    view.read_name_enabled = False
    assert view.read_name_enabled is False
    view.read_name_enabled = True
    assert view.read_name_enabled is True

    view.use_command_enabled = True
    assert view.use_command_enabled is True
    view.use_command_enabled = False
    assert view.use_command_enabled is False

    view.tts_command = "!custom"
    assert view.tts_command == "!custom"

    view.tts_volume = 75
    assert view.tts_volume == 75

    view.tts_speed = 120
    assert view.tts_speed == 120

    assert isinstance(view.overlay_size, int)
    assert isinstance(view.overlay_fade, int)
    assert isinstance(view.overlay_show_bots, bool)
    assert isinstance(view.overlay_show_time, bool)
    assert isinstance(view.overlay_theme, str)
