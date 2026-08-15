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
