# resources\tests\test_chat_overlay_controls.py

import pytest
from PySide6.QtWidgets import QApplication
from backend.services.system.translation_service import TranslationService
from frontend.components.chat.overlay_settings import ChatOverlaySettingsPanel
from frontend.components.chat.chat_mockup import ChatOverlayMockupWidget


@pytest.fixture(scope="module")
def qapp():
    app = QApplication.instance()
    if not app:
        app = QApplication([])
    return app

def test_overlay_settings_panel_compact_and_mockup_reactivity(qapp):
    i18n = TranslationService()
    panel = ChatOverlaySettingsPanel(i18n)

    assert panel.spin_overlay_size is not None
    assert panel.spin_overlay_fade is not None
    assert not hasattr(panel, "spin_overlay_max")
    assert not hasattr(panel, "seg_overlay_entry")

    assert panel.spin_overlay_size.value() == 14
    assert panel.spin_overlay_fade.value() == 15

    mockup = panel.mockup_widget
    assert isinstance(mockup, ChatOverlayMockupWidget)

    assert mockup.show_badges is True
    assert mockup.show_platform is True
    assert mockup.hide_commands is False

    panel.sw_show_badges.setChecked(False)
    assert mockup.show_badges is False

    panel.sw_show_platform.setChecked(False)
    assert mockup.show_platform is False

    panel.sw_hide_commands.setChecked(True)
    assert mockup.hide_commands is True

    mockup.resize(400, 180)
    mockup.repaint()

    panel.seg_overlay_orientation.set_current_value("horizontal")
    assert mockup.orientation == "horizontal"
    mockup.resize(400, 105)
    mockup.repaint()

def test_dual_profile_switching(qapp):
    i18n = TranslationService()
    panel = ChatOverlaySettingsPanel(i18n)

    assert panel.overlay_orientation == "vertical"
    assert panel.vertical_config["flow"] == "bottom-to-top"

    panel.combo_overlay_theme.setCurrentIndex(panel.combo_overlay_theme.findData("dark"))
    panel.spin_overlay_size.setValue(14)
    panel.spin_overlay_fade.setValue(20)
    panel.seg_overlay_flow.set_current_value("top-to-bottom")
    panel.combo_anim_in.setCurrentIndex(panel.combo_anim_in.findData("pop"))

    panel.seg_overlay_orientation.set_current_value("horizontal")
    assert panel.overlay_orientation == "horizontal"
    assert "right-to-left" in panel.seg_overlay_flow._buttons

    panel.combo_overlay_theme.setCurrentIndex(panel.combo_overlay_theme.findData("light"))
    panel.spin_overlay_size.setValue(18)
    panel.spin_overlay_fade.setValue(5)
    panel.seg_overlay_flow.set_current_value("left-to-right")
    panel.combo_anim_in.setCurrentIndex(panel.combo_anim_in.findData("slide"))

    h_cfg = panel.horizontal_config
    assert h_cfg["theme"] == "light"
    assert h_cfg["size"] == 18
    assert h_cfg["fade"] == 5
    assert h_cfg["flow"] == "left-to-right"
    assert h_cfg["anim_in"] == "slide"

    panel.seg_overlay_orientation.set_current_value("vertical")
    assert panel.overlay_orientation == "vertical"

    v_cfg = panel.vertical_config
    assert v_cfg["theme"] == "dark"
    assert v_cfg["size"] == 14
    assert v_cfg["fade"] == 20
    assert v_cfg["flow"] == "top-to-bottom"
    assert v_cfg["anim_in"] == "pop"

    assert panel.combo_overlay_theme.currentData() == "dark"
    assert panel.spin_overlay_size.value() == 14
    assert panel.spin_overlay_fade.value() == 20
    assert panel.seg_overlay_flow.current_value() == "top-to-bottom"
    assert panel.combo_anim_in.currentData() == "pop"

def test_clean_overlay_url_generation(qapp):
    i18n = TranslationService()
    panel = ChatOverlaySettingsPanel(i18n)
    panel.chat_overlay_url = "http://localhost:8090/chat?token=test_token_123"

    panel.seg_overlay_orientation.set_current_value("vertical")
    assert panel.chat_overlay_full_url == "http://localhost:8090/chat?token=test_token_123&orientation=vertical"
    assert "fade=" not in panel.chat_overlay_full_url
    assert "size=" not in panel.chat_overlay_full_url
    assert "show_bots=" not in panel.chat_overlay_full_url

    panel.seg_overlay_orientation.set_current_value("horizontal")
    assert panel.chat_overlay_full_url == "http://localhost:8090/chat?token=test_token_123&orientation=horizontal"
    assert "fade=" not in panel.chat_overlay_full_url

def test_chat_service_and_controller_dual_profiles(qapp):
    from unittest.mock import MagicMock
    from backend.services.chat.chat_service import ChatService
    from backend.controllers.chat_controller import ChatController

    storage = MagicMock()
    storage.load_string.side_effect = lambda k, d="": d
    storage.load_bool.side_effect = lambda k, d=False: d
    storage.save_all = MagicMock()

    tts = MagicMock()
    service = ChatService(tts, storage)
    overlay_cfg = service.get_overlay_settings()
    assert "vertical" in overlay_cfg
    assert "horizontal" in overlay_cfg
    assert "common" in overlay_cfg
    assert overlay_cfg["vertical"]["flow"] == "bottom-to-top"
    assert overlay_cfg["horizontal"]["flow"] == "right-to-left"

    save_payload = {
        "chat_overlay_orientation": "horizontal",
        "chat_overlay_vertical_theme": "glass",
        "chat_overlay_vertical_size": "14",
        "chat_overlay_vertical_fade": "15",
        "chat_overlay_vertical_flow": "bottom-to-top",
        "chat_overlay_vertical_anim_in": "fade",
        "chat_overlay_horizontal_theme": "neon",
        "chat_overlay_horizontal_size": "18",
        "chat_overlay_horizontal_fade": "5",
        "chat_overlay_horizontal_flow": "left-to-right",
        "chat_overlay_horizontal_anim_in": "slide",
        "chat_overlay_show_bots": True,
        "chat_overlay_show_time": False,
    }
    service.save_settings(save_payload)
    assert storage.save_all.called
    saved_batch = storage.save_all.call_args[0][0]
    assert saved_batch["chat_overlay_orientation"] == "horizontal"
    assert saved_batch["chat_overlay_horizontal_theme"] == "neon"
    assert saved_batch["chat_overlay_horizontal_flow"] == "left-to-right"
    assert saved_batch["chat_overlay_horizontal_anim_in"] == "slide"
    assert saved_batch["chat_overlay_vertical_flow"] == "bottom-to-top"

def test_overlay_manager_chat_config_live_sync():
    from backend.services.overlay.overlay_manager import OverlayServerManager
    manager = OverlayServerManager(port=8099)
    test_config = {
        "orientation": "horizontal",
        "vertical": {
            "theme": "glass",
            "size": 14,
            "fade": 15,
            "flow": "bottom-to-top",
            "anim_in": "fade"
        },
        "horizontal": {
            "theme": "cyber",
            "size": 18,
            "fade": 30,
            "flow": "left-to-right",
            "anim_in": "slide"
        },
        "common": {
            "show_bots": True,
            "show_time": True,
            "hide_commands": True,
            "show_badges": False,
            "show_platform": False
        },
        "theme": "cyber",
        "size": "18",
        "fade": "30",
        "flow": "left-to-right",
        "anim_in": "slide",
        "show_bots": True,
        "show_time": True,
        "hide_commands": True,
        "show_badges": False,
        "show_platform": False
    }
    manager.trigger_chat_config_update(test_config)
    assert manager._last_chat_config == test_config

def test_chat_service_get_settings_contains_overlay_keys():
    from unittest.mock import MagicMock
    from backend.services.chat.chat_service import ChatService

    storage = MagicMock()
    storage_data = {
        "chat_overlay_orientation": "horizontal",
        "chat_overlay_horizontal_theme": "cyberpunk",
        "chat_overlay_horizontal_size": "20",
        "chat_overlay_horizontal_fade": "45",
        "chat_overlay_horizontal_flow": "left-to-right",
        "chat_overlay_horizontal_anim_in": "slide",
        "chat_overlay_vertical_theme": "neon",
        "chat_overlay_vertical_size": "16",
        "chat_overlay_vertical_fade": "20",
        "chat_overlay_vertical_flow": "bottom-to-top",
        "chat_overlay_vertical_anim_in": "fade",
        "chat_overlay_show_bots": True,
        "chat_overlay_show_time": True,
        "chat_overlay_show_gifs": False,
        "chat_overlay_big_emotes": True,
        "chat_overlay_hide_commands": True,
        "chat_overlay_show_badges": False,
        "chat_overlay_show_platform": False,
    }
    storage.load_string.side_effect = lambda k, d="": storage_data.get(k, d)
    storage.load_bool.side_effect = lambda k, d=False: storage_data.get(k, d)

    service = ChatService(MagicMock(), storage)
    settings = service.get_settings()

    assert settings["chat_overlay_orientation"] == "horizontal"
    assert settings["chat_overlay_horizontal_theme"] == "cyberpunk"
    assert settings["chat_overlay_horizontal_size"] == "20"
    assert settings["chat_overlay_horizontal_fade"] == "45"
    assert settings["chat_overlay_show_bots"] is True
    assert settings["chat_overlay_show_time"] is True
    assert settings["chat_overlay_show_gifs"] is False
    assert settings["chat_overlay_hide_commands"] is True
    assert settings["chat_overlay_show_badges"] is False
    assert settings["chat_overlay_show_platform"] is False

def test_chat_controller_get_active_overlay_config_preserves_custom_settings_on_startup(qapp):
    from unittest.mock import MagicMock
    from backend.services.chat.chat_service import ChatService
    from backend.controllers.chat_controller import ChatController

    storage = MagicMock()
    custom_saved_data = {
        "chat_overlay_orientation": "horizontal",
        "chat_overlay_horizontal_theme": "neon",
        "chat_overlay_horizontal_size": "18",
        "chat_overlay_horizontal_fade": "25",
        "chat_overlay_horizontal_flow": "left-to-right",
        "chat_overlay_horizontal_anim_in": "slide",
        "chat_overlay_vertical_theme": "glass",
        "chat_overlay_vertical_size": "14",
        "chat_overlay_vertical_fade": "15",
        "chat_overlay_vertical_flow": "bottom-to-top",
        "chat_overlay_vertical_anim_in": "fade",
        "chat_overlay_show_bots": True,
        "chat_overlay_show_time": True,
        "chat_overlay_show_gifs": True,
        "chat_overlay_big_emotes": True,
        "chat_overlay_hide_commands": False,
        "chat_overlay_show_badges": True,
        "chat_overlay_show_platform": True,
    }
    storage.load_string.side_effect = lambda k, d="": custom_saved_data.get(k, d)
    storage.load_bool.side_effect = lambda k, d=False: custom_saved_data.get(k, d)

    service = ChatService(MagicMock(), storage)
    controller = ChatController(
        view=None,
        service=service,
        command_service=MagicMock(),
        spam_service=MagicMock(),
        i18n=MagicMock(),
    )

    controller.sync_settings_cache()
    active_config = controller.get_active_overlay_config()

    assert active_config["orientation"] == "horizontal"
    assert active_config["theme"] == "neon"
    assert active_config["size"] == "18"
    assert active_config["fade"] == "25"
    assert active_config["flow"] == "left-to-right"
    assert active_config["anim_in"] == "slide"
    assert active_config["show_bots"] is True
    assert active_config["show_time"] is True

def test_horizontal_chat_bottom_pinned_and_gif_responsive_rules(qapp):
    import os
    from backend.services.system.translation_service import TranslationService
    from frontend.components.chat.overlay_settings import ChatOverlaySettingsPanel

    html_path = os.path.join("assets", "overlays", "chat", "chat.html")
    assert os.path.exists(html_path)
    with open(html_path, "r", encoding="utf-8") as f:
        html_content = f.read()

    assert "#chat-container.orientation-horizontal {" in html_content
    assert "align-items: flex-end;" in html_content
    assert "align-self: flex-end !important;" in html_content
    assert "#chat-container.orientation-horizontal .chat-gif" in html_content
    assert "max-height: calc(100vh - 22px) !important;" in html_content

    i18n = TranslationService()
    panel = ChatOverlaySettingsPanel(i18n)
    panel.seg_overlay_orientation.set_current_value("horizontal")
    assert "1920 × 80–300 px" in panel.row_copy_obs.lbl_desc.text()

def test_chat_spam_panel_tab_integration(qapp):
    from frontend.views.chat_view import ChatView
    from frontend.components.chat.spam_panel import ChatSpamPanel
    from backend.services.system.translation_service import TranslationService

    i18n = TranslationService(default_lang="es")
    chat_view = ChatView(i18n)

    assert chat_view.tabs.count() == 4
    tab_titles = [chat_view.tabs.tabText(i) for i in range(chat_view.tabs.count())]
    assert i18n.get("chat.tabs.settings") in tab_titles
    assert i18n.get("chat.tabs.muted") in tab_titles
    assert i18n.get("chat.tabs.spam") in tab_titles
    assert i18n.get("chat.tabs.overlay") in tab_titles

    assert hasattr(chat_view, "spam_panel")
    assert isinstance(chat_view.spam_panel, ChatSpamPanel)
    assert len(chat_view.spam_panel.cards) == 6
    assert "caps_protection" in chat_view.spam_panel.cards
    assert "link_protection" in chat_view.spam_panel.cards

    chat_view.set_connected_platforms({"kick": True, "twitch": False, "youtube": False, "tiktok": False})
    assert chat_view.spam_panel.connected_platforms["kick"] is True

    sample_filters = {
        "caps_protection": {"is_active": True, "amount": 8, "platforms": ["kick"]},
        "link_protection": {"is_active": False, "platforms": ["kick", "twitch"]}
    }
    chat_view.spam_panel.populate_filters(sample_filters)
    assert chat_view.spam_panel.cards["caps_protection"].switch.isChecked() is True
    assert chat_view.spam_panel.cards["link_protection"].switch.isChecked() is False
