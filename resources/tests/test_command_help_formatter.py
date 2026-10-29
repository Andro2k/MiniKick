# resources\tests\test_command_help_formatter.py

from backend.handlers.command_help_formatter import CommandHelpFormatter, chunk_messages


class _I18n:
    _TEXTS = {
        "chat.commands_help.sec_chat": "Chat",
        "chat.commands_help.sec_music": "Music",
        "chat.commands_help.sec_widgets": "Widgets",
        "chat.commands_help.sec_moderation": "Mod",
        "chat.commands_help.active_tag": "ON",
        "chat.commands_help.inactive_tag": "OFF",
        "chat.commands_help.active_header": "Active:",
        "chat.commands_help.status_header": "Status:",
        "chat.commands_help.empty_general": "EMPTY",
        "chat.commands_help.empty_category": "No commands in {category}",
    }

    def get(self, key):
        return self._TEXTS[key]


_COMMANDS = [
    {"trigger": "!discord", "response": "discord.gg/x", "is_active": True, "permission": "everyone"},
    {"trigger": "!sr", "response": "[PLUGIN_MUSIC_SR]", "is_active": True, "permission": "everyone"},
    {"trigger": "!pause", "response": "[PLUGIN_MUSIC_PAUSE]", "is_active": False, "permission": "moderator"},
    {"trigger": "!death", "response": "[PLUGIN_WIDGET_DEATH]", "is_active": True, "permission": "everyone"},
    {"trigger": "!ttsmute", "response": "[PLUGIN_CHAT_TTS_MUTE]", "is_active": True, "permission": "moderator"},
]


def _fmt():
    return CommandHelpFormatter(_I18n())


def test_no_commands_returns_empty_message():
    assert _fmt().format([], "", False) == ["EMPTY"]


def test_overview_hides_moderation_for_viewers_and_shows_it_to_mods():
    viewer = _fmt().format(_COMMANDS, "", False)
    assert viewer == ["Active: Chat: !discord | Music: !sr | Widgets: !death"]
    assert "!ttsmute" in _fmt().format(_COMMANDS, "", True)[0]


def test_all_mode_lists_inactive_commands_with_markers():
    msg = _fmt().format(_COMMANDS, "todos", False)[0]
    assert msg.startswith("Status:")
    assert "Music: [✅ !sr | ❌ !pause]" in msg


def test_specific_category_uses_alias_and_tags():
    assert _fmt().format(_COMMANDS, "musica", False) == ["Music: ON: !sr | OFF: !pause"]


def test_moderation_category_is_silent_for_non_mods():
    assert _fmt().format(_COMMANDS, "mod", False) == []
    assert _fmt().format(_COMMANDS, "mod", True) == ["Mod: ON: !ttsmute"]


def test_empty_category_message_uses_label():
    only_chat = [_COMMANDS[0]]
    assert _fmt().format(only_chat, "widgets", False) == ["No commands in Widgets"]


def test_overview_with_nothing_active_returns_empty_message():
    inactive = [{**_COMMANDS[0], "is_active": False}]
    assert _fmt().format(inactive, "", False) == ["EMPTY"]


def test_chunk_messages_respects_limit_and_keeps_every_command():
    sections = [f"S{n}: " + ", ".join(f"!c{n}_{i}" for i in range(25)) for n in range(3)]
    chunks = chunk_messages("H:", sections, max_chars=120)
    assert len(chunks) > 1 and all(len(c) <= 120 for c in chunks)
    joined = " ".join(chunks)
    assert all(f"!c{n}_{i}" in joined for n in range(3) for i in range(25))


def test_chunk_messages_single_message_when_it_fits():
    assert chunk_messages("H:", ["a", "b"], max_chars=380) == ["H: a | b"]
    assert chunk_messages("H:", [], max_chars=380) == []
