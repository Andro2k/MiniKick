# resources\tests\test_chat_controller.py

import pytest
from unittest.mock import MagicMock
from PySide6.QtWidgets import QApplication
from backend.controllers.chat_controller import ChatController, _build_command_response_map, _parse_mute_args, _parse_block_args
from backend.services.chat.chat_pipeline import ChatMessageDTO
from backend.services.system.translation_service import TranslationService


@pytest.fixture(scope="module")
def qapp():
    app = QApplication.instance()
    if not app:
        app = QApplication([])
    return app

@pytest.fixture
def mock_dependencies():
    view = MagicMock()
    view.is_web_provider = False
    view.tts_enabled = True
    view.read_name_enabled = True
    view.use_command_enabled = False
    view.tts_command = "!tts"
    view.tts_volume = 100
    view.tts_speed = 100
    view.get_role_voices.return_value = {}

    service = MagicMock()
    service.get_settings.return_value = {
        "enabled": True,
        "read_name": True,
        "use_command": False,
        "command": "!tts",
        "provider": "piper",
        "volume": 100,
        "speed": 100,
        "ignored_users": "bot1,bot2",
        "banned_words": "badword,toxic",
        "mod_mute_command_enabled": True,
        "mod_block_command_enabled": True,
        "platform_kick": True,
        "platform_twitch": True,
    }
    service.get_overlay_settings.return_value = {
        "vertical": {"theme": "glass", "size": 14, "fade": 15, "flow": "bottom-to-top", "anim_in": "fade"},
        "horizontal": {"theme": "glass", "size": 14, "fade": 15, "flow": "right-to-left", "anim_in": "fade"},
        "common": {"show_bots": False, "show_time": False, "big_emotes": True, "show_gifs": True, "hide_commands": False, "show_badges": True, "show_platform": True},
        "orientation": "vertical",
    }

    command_service = MagicMock()
    command_service.get_all_commands.return_value = []
    command_service.process_incoming_message.return_value = (False, "", {}, "")

    spam_service = MagicMock()
    spam_service.is_spam.return_value = False

    i18n = TranslationService()
    toast = MagicMock()
    giphy_service = MagicMock()

    return {
        "view": view,
        "service": service,
        "command_service": command_service,
        "spam_service": spam_service,
        "i18n": i18n,
        "toast": toast,
        "giphy_service": giphy_service,
    }

def test_command_response_map_indexing():
    raw_commands = [
        {"trigger": "!tts", "response": "[PLUGIN_CHAT_TTS]"},
        {"trigger": "!systts", "response": "[PLUGIN_CHAT_SYSTTS]"},
        {"trigger": "!custom", "response": "Hello World"},
    ]
    cmd_map = _build_command_response_map(raw_commands)

    assert "[PLUGIN_CHAT_TTS]" in cmd_map
    assert cmd_map["[PLUGIN_CHAT_TTS]"]["trigger"] == "!tts"
    assert "[PLUGIN_CHAT_SYSTTS]" in cmd_map
    assert "Hello World" in cmd_map
    assert "[UNKNOWN]" not in cmd_map

def test_pure_mod_argument_parsers():
    assert _parse_mute_args("!ttsmute", "!ttsmute @spammer") == (False, "spammer")
    assert _parse_mute_args("!ttsmute", "!ttsmute +spammer") == (False, "spammer")
    assert _parse_mute_args("!ttsmute", "!ttsmute add @spammer") == (False, "spammer")
    assert _parse_mute_args("!ttsmute", "!ttsmute -spammer") == (True, "spammer")
    assert _parse_mute_args("!ttsmute", "!ttsmute del @spammer") == (True, "spammer")
    assert _parse_mute_args("!ttsunmute", "!ttsunmute @spammer") == (True, "spammer")
    assert _parse_mute_args("!unmutetts", "!unmutetts") == (True, "")

    assert _parse_block_args("!ttsblock", "!ttsblock bad word") == (False, "bad word")
    assert _parse_block_args("!ttsblock", "!ttsblock add toxic word") == (False, "toxic word")
    assert _parse_block_args("!ttsblock", "!ttsblock -bad word") == (True, "bad word")
    assert _parse_block_args("!ttsblock", "!ttsblock del bad word") == (True, "bad word")
    assert _parse_block_args("!ttsunblock", "!ttsunblock free word") == (True, "free word")
    assert _parse_block_args("!unblockword", "!unblockword") == (True, "")

def test_chat_controller_init_and_system_command_upsert(qapp, mock_dependencies):
    d = mock_dependencies
    controller = ChatController(
        view=d["view"],
        service=d["service"],
        command_service=d["command_service"],
        spam_service=d["spam_service"],
        i18n=d["i18n"],
        toast_manager=d["toast"],
        giphy_service=d["giphy_service"],
    )

    assert controller.giphy_service is d["giphy_service"]

    saved_responses = [call[1]["response"] for call in d["command_service"].save_command.call_args_list]
    assert "[PLUGIN_CHAT_TTS]" in saved_responses
    assert "[PLUGIN_CHAT_SYSTTS]" in saved_responses
    assert "[PLUGIN_CHAT_TTS_MUTE]" in saved_responses
    assert "[PLUGIN_CHAT_TTS_BLOCK]" in saved_responses
    assert "[PLUGIN_CHAT_GIF]" in saved_responses

def test_chat_controller_pipeline_spam_blocking(qapp, mock_dependencies):
    d = mock_dependencies
    controller = ChatController(
        view=d["view"],
        service=d["service"],
        command_service=d["command_service"],
        spam_service=d["spam_service"],
        i18n=d["i18n"],
    )

    spam_spy = MagicMock()
    controller.spam_blocked.connect(spam_spy)

    d["spam_service"].is_spam.return_value = True

    dto = ChatMessageDTO(
        user="BadActor",
        content="BUY FOLLOWERS HERE",
        badges=[],
        color="#FFF",
        msg_id="1",
        sender_id=10,
        timestamp="12:00:00",
        platform="kick"
    )

    controller.process_message(dto)

    assert dto.is_cancelled is True
    spam_spy.assert_called_once()
    d["service"].speak.assert_not_called()

def test_chat_controller_pipeline_tts_execution(qapp, mock_dependencies):
    d = mock_dependencies
    controller = ChatController(
        view=d["view"],
        service=d["service"],
        command_service=d["command_service"],
        spam_service=d["spam_service"],
        i18n=d["i18n"],
    )

    dto = ChatMessageDTO(
        user="Viewer123",
        content="Hola a todos en el stream!",
        badges=[],
        color="#00FF00",
        msg_id="2",
        sender_id=20,
        timestamp="12:01:00",
        platform="kick"
    )

    controller.process_message(dto)

    assert dto.is_cancelled is False
    d["service"].speak.assert_called_once()
    spoken_text = d["service"].speak.call_args[0][0]
    assert "Viewer123" in spoken_text
    assert "Hola a todos en el stream!" in spoken_text

def test_chat_controller_pipeline_tts_skipped_for_bot_and_banned(qapp, mock_dependencies):
    d = mock_dependencies
    controller = ChatController(
        view=d["view"],
        service=d["service"],
        command_service=d["command_service"],
        spam_service=d["spam_service"],
        i18n=d["i18n"],
    )

    dto_bot = ChatMessageDTO(
        user="bot1",
        content="I am a bot message",
        badges=[],
        color="#FFF",
        msg_id="3",
        sender_id=30,
        timestamp="12:02:00",
        platform="kick"
    )
    controller.process_message(dto_bot)
    d["service"].speak.assert_not_called()

    dto_banned = ChatMessageDTO(
        user="Viewer",
        content="This contains badword here",
        badges=[],
        color="#FFF",
        msg_id="4",
        sender_id=40,
        timestamp="12:03:00",
        platform="kick"
    )
    controller.process_message(dto_banned)
    d["service"].speak.assert_not_called()

def test_chat_controller_mod_systts_command(qapp, mock_dependencies):
    d = mock_dependencies
    controller = ChatController(
        view=d["view"],
        service=d["service"],
        command_service=d["command_service"],
        spam_service=d["spam_service"],
        i18n=d["i18n"],
    )

    state_spy = MagicMock()
    controller.tts_state_changed.connect(state_spy)

    controller._handle_systts_command("ModUser", "off", platform="kick")
    assert controller._tts_enabled is False
    d["service"].set_tts_enabled.assert_called_with(False)
    state_spy.assert_called_with(False)
    d["command_service"].send_response.assert_called()

    controller._handle_systts_command("ModUser", "on", platform="kick")
    assert controller._tts_enabled is True
    d["service"].set_tts_enabled.assert_called_with(True)
    state_spy.assert_called_with(True)

def test_chat_controller_mod_mute_and_unmute(qapp, mock_dependencies):
    d = mock_dependencies
    controller = ChatController(
        view=d["view"],
        service=d["service"],
        command_service=d["command_service"],
        spam_service=d["spam_service"],
        i18n=d["i18n"],
    )

    dto_mute = ChatMessageDTO(
        user="ModUser",
        content="!ttsmute @annoying_user",
        badges=["moderator"],
        color="#00F",
        msg_id="5",
        sender_id=50,
        timestamp="12:04:00",
        platform="kick"
    )

    controller._handle_plugin_ttsmute(dto_mute, prefix="!ttsmute")
    assert "annoying_user" in controller.filter_handler.muted_bots
    d["command_service"].send_response.assert_called()

    dto_unmute = ChatMessageDTO(
        user="ModUser",
        content="!ttsunmute @annoying_user",
        badges=["moderator"],
        color="#00F",
        msg_id="6",
        sender_id=50,
        timestamp="12:05:00",
        platform="kick"
    )
    controller._handle_plugin_ttsunmute(dto_unmute, prefix="!ttsunmute")
    assert "annoying_user" not in controller.filter_handler.muted_bots

def test_chat_controller_mod_block_and_unblock(qapp, mock_dependencies):
    d = mock_dependencies
    controller = ChatController(
        view=d["view"],
        service=d["service"],
        command_service=d["command_service"],
        spam_service=d["spam_service"],
        i18n=d["i18n"],
    )

    dto_block = ChatMessageDTO(
        user="ModUser",
        content="!ttsblock prohibited_term",
        badges=["moderator"],
        color="#00F",
        msg_id="7",
        sender_id=50,
        timestamp="12:06:00",
        platform="kick"
    )

    controller._handle_plugin_ttsblock(dto_block, prefix="!ttsblock")
    assert "prohibited_term" in controller.filter_handler.banned_words
    d["command_service"].send_response.assert_called()

    dto_unblock = ChatMessageDTO(
        user="ModUser",
        content="!ttsunblock prohibited_term",
        badges=["moderator"],
        color="#00F",
        msg_id="8",
        sender_id=50,
        timestamp="12:07:00",
        platform="kick"
    )
    controller._handle_plugin_ttsunblock(dto_unblock, prefix="!ttsunblock")
    assert "prohibited_term" not in controller.filter_handler.banned_words
