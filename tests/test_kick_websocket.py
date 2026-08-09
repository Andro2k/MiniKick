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


def test_chat_socket_manager_parse_poll_update_frame():
    received_polls = []

    def mock_poll_update(poll_data):
        received_polls.append(poll_data)

    manager = ChatSocketManager("us2", "eb12322a5d259020583b")
    manager._on_poll_update = mock_poll_update
    manager._running = True

    sample_poll_frame = json.dumps({
        "event": "App\\Events\\PollUpdateEvent",
        "data": json.dumps({
            "poll": {
                "title": "¿Cuál es tu juego favorito?",
                "options": [
                    {"id": 1, "label": "Minecraft", "votes": 15},
                    {"id": 2, "label": "Valorant", "votes": 30}
                ],
                "duration": 60,
                "remaining": 45
            }
        })
    })

    manager._on_raw_frame(None, sample_poll_frame)

    assert len(received_polls) == 1
    poll = received_polls[0]
    assert poll["title"] == "¿Cuál es tu juego favorito?"
    assert len(poll["options"]) == 2
    assert poll["options"][1]["votes"] == 30


def test_chat_socket_manager_parse_poll_delete_frame():
    deleted_calls = []

    def mock_poll_delete():
        deleted_calls.append(True)

    manager = ChatSocketManager("us2", "eb12322a5d259020583b")
    manager._on_poll_delete = mock_poll_delete
    manager._running = True

    sample_delete_frame = json.dumps({
        "event": "App\\Events\\PollDeleteEvent",
        "data": "[]"
    })

    manager._on_raw_frame(None, sample_delete_frame)

    assert len(deleted_calls) == 1
    assert deleted_calls[0] is True


def test_chat_socket_manager_parse_pinned_events():
    created_pinned = []
    deleted_pinned = []

    def mock_pinned_created(data):
        created_pinned.append(data)

    def mock_pinned_deleted():
        deleted_pinned.append(True)

    manager = ChatSocketManager("us2", "eb12322a5d259020583b")
    manager._on_pinned_created = mock_pinned_created
    manager._on_pinned_deleted = mock_pinned_deleted
    manager._running = True

    sample_created = json.dumps({
        "event": "App\\Events\\PinnedMessageCreatedEvent",
        "data": json.dumps({
            "pinned_message": {
                "id": "pin_1",
                "content": "¡Leed las reglas del chat!",
                "sender": {"username": "Moderador1"}
            }
        })
    })

    manager._on_raw_frame(None, sample_created)
    assert len(created_pinned) == 1
    assert created_pinned[0]["content"] == "¡Leed las reglas del chat!"

    sample_deleted = json.dumps({
        "event": "App\\Events\\PinnedMessageDeletedEvent",
        "data": "{}"
    })

    manager._on_raw_frame(None, sample_deleted)
    assert len(deleted_pinned) == 1


def test_chat_socket_manager_parse_badges_v2_level():
    received_data = []

    def mock_callback(user, msg, badges, color, msg_id, sender_id):
        received_data.append((user, msg, badges, color, msg_id, sender_id))

    manager = ChatSocketManager("us2", "eb12322a5d259020583b")
    manager._callback = mock_callback
    manager._running = True

    sample_frame = json.dumps({
        "event": "App\\Events\\ChatMessageEvent",
        "data": json.dumps({
            "id": "msg_lvl",
            "content": "Hola con nivel",
            "sender": {
                "id": 55,
                "username": "NivelUser",
                "identity": {
                    "color": "#75FD46",
                    "badges": [{"type": "subscriber"}],
                    "badges_v2": [{"name": "level", "metadata": {"level": 25}}]
                }
            }
        })
    })

    manager._on_raw_frame(None, sample_frame)
    assert len(received_data) == 1
    _, _, badges, _, _, _ = received_data[0]
    assert badges == ["subscriber", "level_25"]
