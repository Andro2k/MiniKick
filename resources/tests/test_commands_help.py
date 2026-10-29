# resources\tests\test_commands_help.py

import pytest
from unittest.mock import MagicMock
from PySide6.QtWidgets import QApplication
from backend.services.system.translation_service import TranslationService
from backend.controllers.chat_controller import ChatController
from backend.services.chat import ChatMessageDTO

@pytest.fixture(scope="session")
def qapp():
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    return app

@pytest.fixture
def i18n():
    return TranslationService()

def test_handle_plugin_commands_active_summary(qapp, i18n):
    mock_service = MagicMock()
    mock_cmd_service = MagicMock()
    mock_spam = MagicMock()

    mock_cmd_service.get_all_commands.return_value = [
        {"trigger": "!discord", "response": "discord.gg/test", "is_active": True, "permission": "everyone"},
        {"trigger": "!redes", "response": "instagram.com/test", "is_active": True, "permission": "everyone"},
        {"trigger": "!sr", "response": "[PLUGIN_MUSIC_SR]", "is_active": True, "permission": "everyone"},
        {"trigger": "!skip", "response": "[PLUGIN_MUSIC_SKIP]", "is_active": True, "permission": "moderator"},
        {"trigger": "!death", "response": "[PLUGIN_WIDGET_DEATH]", "is_active": True, "permission": "everyone"},
        {"trigger": "!ttsmute", "response": "[PLUGIN_CHAT_TTS_MUTE]", "is_active": True, "permission": "moderator"},
    ]

    controller = ChatController(
        view=None,
        service=mock_service,
        command_service=mock_cmd_service,
        spam_service=mock_spam,
        i18n=i18n
    )

    dto_viewer = ChatMessageDTO(
        user="ViewerNormal",
        content="!commands",
        badges=[],
        color="#ffffff",
        msg_id="1",
        sender_id=123
    )
    controller._handle_plugin_commands(dto_viewer, "!commands")

    assert mock_cmd_service.send_response.called
    sent_msg = mock_cmd_service.send_response.call_args[0][0]
    assert "!discord" in sent_msg
    assert "!redes" in sent_msg
    assert "!sr" in sent_msg
    assert "!death" in sent_msg
    assert "!ttsmute" not in sent_msg

    mock_cmd_service.send_response.reset_mock()
    dto_mod = ChatMessageDTO(
        user="ModUser",
        content="!commands",
        badges=["moderator"],
        color="#ffffff",
        msg_id="2",
        sender_id=456
    )
    controller._handle_plugin_commands(dto_mod, "!commands")
    sent_mod_msg = mock_cmd_service.send_response.call_args[0][0]
    assert "!ttsmute" in sent_mod_msg

def test_handle_plugin_commands_all_status(qapp, i18n):
    mock_service = MagicMock()
    mock_cmd_service = MagicMock()
    mock_spam = MagicMock()

    mock_cmd_service.get_all_commands.return_value = [
        {"trigger": "!discord", "response": "discord.gg/test", "is_active": True, "permission": "everyone"},
        {"trigger": "!reglas", "response": "respeta a todos", "is_active": False, "permission": "everyone"},
        {"trigger": "!sr", "response": "[PLUGIN_MUSIC_SR]", "is_active": True, "permission": "everyone"},
        {"trigger": "!pause", "response": "[PLUGIN_MUSIC_PAUSE]", "is_active": False, "permission": "moderator"},
    ]

    controller = ChatController(
        view=None,
        service=mock_service,
        command_service=mock_cmd_service,
        spam_service=mock_spam,
        i18n=i18n
    )

    dto = ChatMessageDTO(
        user="Streamer",
        content="!commands all",
        badges=["broadcaster"],
        color="#ffffff",
        msg_id="3",
        sender_id=789
    )
    controller._handle_plugin_commands(dto, "!commands")

    assert mock_cmd_service.send_response.called
    sent_msg = mock_cmd_service.send_response.call_args[0][0]
    assert "✅" in sent_msg
    assert "❌" in sent_msg
    assert "!discord" in sent_msg
    assert "!reglas" in sent_msg
    assert "!sr" in sent_msg

def test_handle_plugin_commands_specific_category(qapp, i18n):
    mock_service = MagicMock()
    mock_cmd_service = MagicMock()
    mock_spam = MagicMock()

    mock_cmd_service.get_all_commands.return_value = [
        {"trigger": "!sr", "response": "[PLUGIN_MUSIC_SR]", "is_active": True, "permission": "everyone"},
        {"trigger": "!pause", "response": "[PLUGIN_MUSIC_PAUSE]", "is_active": False, "permission": "moderator"},
        {"trigger": "!discord", "response": "discord.gg/test", "is_active": True, "permission": "everyone"},
    ]

    controller = ChatController(
        view=None,
        service=mock_service,
        command_service=mock_cmd_service,
        spam_service=mock_spam,
        i18n=i18n
    )

    dto = ChatMessageDTO(
        user="Viewer",
        content="!commands musica",
        badges=[],
        color="#ffffff",
        msg_id="4",
        sender_id=101112
    )
    controller._handle_plugin_commands(dto, "!commands")

    assert mock_cmd_service.send_response.called
    sent_msg = mock_cmd_service.send_response.call_args[0][0]
    assert "!sr" in sent_msg
    assert "!pause" in sent_msg
    assert "!discord" not in sent_msg

def test_send_chunked_command_responses_limits():
    from backend.handlers.command_help_formatter import chunk_messages

    large_sections = [
        f"Seccion1: " + ", ".join([f"!cmd{i}" for i in range(25)]),
        f"Seccion2: " + ", ".join([f"!musica{i}" for i in range(25)]),
        f"Seccion3: " + ", ".join([f"!widget{i}" for i in range(25)])
    ]

    chunks = chunk_messages("📖 Test:", large_sections, max_chars=150)
    assert len(chunks) > 1
    assert all(len(c) <= 150 for c in chunks)

def test_bot_messages_do_not_trigger_commands_or_autoresponses(qapp, i18n):
    mock_service = MagicMock()
    mock_cmd_service = MagicMock()
    mock_spam = MagicMock()
    mock_spam.filter_handler.is_bot.side_effect = lambda u, b=None: (u or "").strip().lower().lstrip("@") in ("minikick", "nightbot", "botrix")

    controller = ChatController(
        view=None,
        service=mock_service,
        command_service=mock_cmd_service,
        spam_service=mock_spam,
        i18n=i18n
    )

    dto_bot = ChatMessageDTO(
        user="@MiniKick",
        content="📖 Comandos activos: 💬 Chat: !discord, !commands | 🎵 Música: !sr",
        badges=["bot"],
        color="#53fc18",
        msg_id="kick_bot_msg_1",
        sender_id=999999,
        platform="kick"
    )

    controller._step_commands(dto_bot)

    assert not mock_cmd_service.process_incoming_message.called
    assert not mock_cmd_service.send_response.called

def test_command_service_rejects_bots():
    from backend.services.chat import CommandService
    mock_storage = MagicMock()
    mock_storage.load_all.return_value = [
        {"trigger": "!discord", "response": "discord.gg/test", "is_active": True, "cooldown": 5, "aliases": "", "is_regex": False, "permission": "everyone", "apply_kick": True, "apply_twitch": True, "apply_youtube": True, "apply_tiktok": True}
    ]

    service = CommandService(mock_storage)

    handled, _, _, _ = service.process_incoming_message("@MiniKick", "!discord", badges=[], platform="kick")
    assert not handled

    handled_nightbot, _, _, _ = service.process_incoming_message("Nightbot", "!discord", badges=[], platform="twitch")
    assert not handled_nightbot

    handled_badge, _, _, _ = service.process_incoming_message("SomeUser", "!discord", badges=["bot"], platform="kick")
    assert not handled_badge

    handled_user, _, cmd_info, _ = service.process_incoming_message("NormalViewer", "!discord", badges=[], platform="kick")
    assert handled_user
    assert cmd_info.get("trigger") == "!discord"

def test_register_system_commands_emits_commands_changed(qapp, i18n):
    mock_service = MagicMock()
    mock_cmd_service = MagicMock()
    mock_spam = MagicMock()

    mock_cmd_service.get_all_commands.return_value = []

    controller = ChatController(
        view=None,
        service=mock_service,
        command_service=mock_cmd_service,
        spam_service=mock_spam,
        i18n=i18n
    )

    controller._register_system_commands()

    assert mock_cmd_service.commands_changed.emit.called
