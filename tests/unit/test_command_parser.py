# tests\unit\test_command_parser.py

from frontend.common.utils import validate_trigger_prefix

def test_validate_trigger_prefix_valid():
    assert validate_trigger_prefix("!tts") is True
    assert validate_trigger_prefix("!sr") is True
    assert validate_trigger_prefix("!skip") is True
    assert validate_trigger_prefix("") is True

def test_validate_trigger_prefix_invalid():
    assert validate_trigger_prefix("tts") is False
    assert validate_trigger_prefix("sr") is False

def test_command_service_platform_routing():
    from backend.services.chat.command_service import CommandService

    class DummyStorage:
        def load_all(self):
            return [{
                "trigger": "!hola",
                "response": "Hola {user}!",
                "is_active": True,
                "cooldown": 0,
                "aliases": "",
                "is_regex": False,
                "permission": "everyone"
            }]
        def log_command_execution(self, trigger, user):
            pass

    class DummyTwitchWorker:
        def __init__(self):
            self.last_msg = ""
        def send_bot_message(self, text):
            self.last_msg = text

    class DummyKickClient:
        def __init__(self):
            self.last_msg = ""
        def post_chat_message(self, content, msg_type="bot"):
            self.last_msg = content

    service = CommandService(commands_storage=DummyStorage())
    service.twitch_worker = DummyTwitchWorker()
    service.api_client = DummyKickClient()

    responses = []
    service.response_generated.connect(lambda text, plat: responses.append((text, plat)))

    service.process_incoming_message("TwitchViewer", "!hola", [], platform="twitch")
    assert service.twitch_worker.last_msg == "Hola TwitchViewer!"
    assert service.api_client.last_msg == ""
    assert ("Hola TwitchViewer!", "twitch") in responses

    service.process_incoming_message("KickViewer", "!hola", [], platform="kick")
    assert service.api_client.last_msg == "Hola KickViewer!"
    assert ("Hola KickViewer!", "kick") in responses

def test_command_view_filter_and_toggle_preservation():
    from PySide6.QtWidgets import QApplication
    from frontend.views.command_view import CommandView
    from backend.services.system.translation_service import TranslationService

    app = QApplication.instance() or QApplication([])
    i18n = TranslationService(default_lang="es")
    view = CommandView(i18n=i18n)

    initial_commands = [
        {"trigger": "!test1", "response": "resp 1", "is_active": True, "cooldown": 3, "aliases": "", "is_regex": False, "permission": "everyone"},
        {"trigger": "!test2", "response": "resp 2", "is_active": True, "cooldown": 3, "aliases": "", "is_regex": False, "permission": "everyone"}
    ]
    view.populate_table(initial_commands)

    # Filter with search
    view.txt_search.setText("test1")
    assert view.table.rowCount() == 1

    from frontend.widgets import ModernSwitch
    action_cell = view.table.cellWidget(0, 4)
    switch = action_cell.findChild(ModernSwitch)
    assert switch is not None
    switch.setChecked(False)

    # Clear search
    view.txt_search.setText("")
    assert view.table.rowCount() == 2

    # Verify that test1 is still inactive in view's state
    cmd_1 = next(c for c in view._raw_commands if c["trigger"] == "!test1")
    assert cmd_1["is_active"] is False

def test_widget_controller_twitch_platform_routing():
    from unittest.mock import MagicMock
    from backend.controllers.widget_controller import WidgetController
    from backend.services.system.translation_service import TranslationService

    i18n = TranslationService(default_lang="es")
    widget_service = MagicMock()
    widget_service.update_death_count.return_value = 5
    widget_service.get_widget.return_value = {"is_active": True, "config": {}}

    command_service = MagicMock()
    ctrl = WidgetController(view=None, widget_service=widget_service, command_service=command_service, i18n=i18n)

    # Dispatch death command from twitch
    ctrl.handle_widget_command("[PLUGIN_WIDGET_DEATH]", "TwitchUser", "!death +", "!death", platform="twitch")

    command_service.send_response.assert_called_once()
    _, kwargs = command_service.send_response.call_args
    assert kwargs.get("platform") == "twitch"
