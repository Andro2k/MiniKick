# tests\test_kick_websocket.py

import json
from backend.providers.chat.kick_websocket import ChatSocketManager

try:
    from backend.config.api_keys import KICK_PUSHER_CLUSTER, KICK_PUSHER_KEY
except ImportError:
    KICK_PUSHER_CLUSTER = "us2"
    KICK_PUSHER_KEY = "32cbd69e4b950bf97679"

def test_chat_socket_manager_initialization():
    manager = ChatSocketManager(KICK_PUSHER_CLUSTER, KICK_PUSHER_KEY)
    assert manager.cluster == KICK_PUSHER_CLUSTER
    assert manager.key == KICK_PUSHER_KEY
    assert manager._running is False


def test_chat_socket_manager_parse_chat_message_frame():
    received_data = []

    def mock_callback(user, msg, badges, color, msg_id, sender_id):
        received_data.append((user, msg, badges, color, msg_id, sender_id))

    manager = ChatSocketManager("us2", "eb12322a5d259020583b")
    manager._callback = mock_callback
    manager._running = True

    sample_pusher_frame = json.dumps({
        "event": "App\\Events\\ChatMessageEvent",
        "data": json.dumps({
            "id": "msg_999",
            "content": "¡Hola desde el test!",
            "sender": {
                "id": 12345,
                "username": "TestUser",
                "identity": {
                    "color": "#00FF00",
                    "badges": [{"type": "subscriber"}, {"type": "moderator"}]
                }
            }
        })
    })

    manager._on_raw_frame(None, sample_pusher_frame)

    assert len(received_data) == 1
    user, msg, badges, color, msg_id, sender_id = received_data[0]
    assert user == "TestUser"

    assert msg == "¡Hola desde el test!"
    assert badges == ["subscriber", "moderator"]
    assert color == "#00FF00"
    assert msg_id == "msg_999"
    assert sender_id == 12345
