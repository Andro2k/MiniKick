# resources\tests\test_command_service_helpers.py

import pytest
from PySide6.QtWidgets import QApplication

from backend.services.chat.commands_service import CommandService


@pytest.fixture(scope="module")
def qapp():
    return QApplication.instance() or QApplication([])


class _Storage:
    def __init__(self, commands=None):
        self.commands = list(commands or [])

    def load_all(self):
        return [dict(c) for c in self.commands]

    def save_command(self, trigger, response, is_active, cooldown, aliases, is_regex, permission, *args):
        self.commands = [c for c in self.commands if c["trigger"] != trigger]
        self.commands.append({
            "trigger": trigger, "response": response, "is_active": is_active, "cooldown": cooldown,
            "aliases": aliases, "is_regex": is_regex, "permission": permission,
            "apply_kick": args[0] if args else True,
        })

    def delete_command(self, trigger):
        self.commands = [c for c in self.commands if c["trigger"] != trigger]

    def get_command_by_trigger(self, trigger):
        return next((dict(c) for c in self.commands if c["trigger"] == trigger), None)


_GIF_CFG = {"trigger": "!gif", "cooldown": 2, "aliases": "!giphy", "is_regex": False, "permission": "everyone"}


def _cmd(svc, tag):
    return svc.get_command_by_response(tag)


def test_ensure_command_creates_with_defaults_and_requested_state(qapp):
    svc = CommandService(commands_storage=_Storage())
    svc.ensure_command("[PLUGIN_CHAT_GIF]", _GIF_CFG, is_active=False)

    cmd = _cmd(svc, "[PLUGIN_CHAT_GIF]")
    assert cmd["trigger"] == "!gif" and cmd["is_active"] is False and cmd["cooldown"] == 2


def test_ensure_command_merges_missing_aliases_and_keeps_user_settings(qapp):
    svc = CommandService(commands_storage=_Storage([
        {"trigger": "!gif", "response": "[PLUGIN_CHAT_GIF]", "is_active": False,
         "cooldown": 9, "aliases": "!mine", "is_regex": False, "permission": "vip"},
    ]))
    svc.ensure_command("[PLUGIN_CHAT_GIF]", _GIF_CFG, is_active=True)

    cmd = _cmd(svc, "[PLUGIN_CHAT_GIF]")
    assert cmd["aliases"] == "!mine,!giphy"
    assert (cmd["is_active"], cmd["cooldown"], cmd["permission"]) == (False, 9, "vip")


def test_set_command_active_by_tag_toggles_and_reports_change(qapp):
    svc = CommandService(commands_storage=_Storage())
    svc.ensure_command("[PLUGIN_CHAT_GIF]", _GIF_CFG, is_active=True)

    assert svc.set_command_active_by_tag("[PLUGIN_CHAT_GIF]", True, _GIF_CFG) is False
    assert svc.set_command_active_by_tag("[PLUGIN_CHAT_GIF]", False, _GIF_CFG) is True
    assert _cmd(svc, "[PLUGIN_CHAT_GIF]")["is_active"] is False


def test_set_command_active_by_tag_recreates_missing_only_when_activating(qapp):
    svc = CommandService(commands_storage=_Storage())

    assert svc.set_command_active_by_tag("[PLUGIN_CHAT_GIF]", False, _GIF_CFG) is False
    assert _cmd(svc, "[PLUGIN_CHAT_GIF]") is None
    assert svc.set_command_active_by_tag("[PLUGIN_CHAT_GIF]", True, _GIF_CFG) is True
    assert _cmd(svc, "[PLUGIN_CHAT_GIF]")["trigger"] == "!gif"


def test_silent_updates_blocks_commands_changed_and_restores_state(qapp):
    svc = CommandService(commands_storage=_Storage())
    emitted = []
    svc.commands_changed.connect(lambda: emitted.append(1))

    with svc.silent_updates():
        svc.save_command_from(_GIF_CFG, response="[PLUGIN_CHAT_GIF]")
    assert emitted == []

    svc.save_command_from(_GIF_CFG, response="[PLUGIN_CHAT_GIF]", is_active=False)
    assert emitted
