# tests\test_twitch_websocket.py

from backend.providers.chat.twitch_websocket import TwitchSocketManager

def test_twitch_socket_manager_initialization():
    manager = TwitchSocketManager(token="oauth:testtoken123", nick="bot_test")
    assert manager.token == "testtoken123"
    assert manager.nick == "bot_test"

def test_twitch_parse_privmsg_tags():
    manager = TwitchSocketManager()
    parsed_result = []

    def mock_callback(user, msg, badges, color, msg_id, sender_id):
        parsed_result.append({
            "user": user,
            "msg": msg,
            "badges": badges,
            "color": color,
            "msg_id": msg_id,
            "sender_id": sender_id
        })

    manager._callback = mock_callback

    raw_line = (
        "@badges=broadcaster/1,subscriber/12;color=#9146FF;display-name=StreamerName;"
        "emotes=;id=msg-uuid-999;mod=0;room-id=12345;subscriber=1;user-id=8888 "
        ":streamername!streamername@streamername.tmi.twitch.tv PRIVMSG #streamerchannel :Hola desde Twitch!"
    )

    manager._parse_privmsg(raw_line)

    assert len(parsed_result) == 1
    res = parsed_result[0]
    assert res["user"] == "StreamerName"
    assert res["msg"] == "Hola desde Twitch!"
    assert res["color"] == "#9146FF"
    assert res["msg_id"] == "msg-uuid-999"
    assert res["sender_id"] == 8888
    assert "broadcaster" in res["badges"]
    assert "subscriber" in res["badges"]

def test_twitch_api_client_fetch_user_data(monkeypatch):
    from backend.providers.chat.twitch_client import TwitchAPIClient
    
    class DummyAuth:
        def get_tokens(self):
            return {"access_token": "mock_token"}

    class DummyResponse:
        def raise_for_status(self):
            pass
        def json(self):
            return {
                "data": [
                    {
                        "id": "99999",
                        "login": "streamer_twitch",
                        "display_name": "StreamerTwitch",
                        "description": "Streamer de prueba",
                        "profile_image_url": "http://example.com/pic.jpg",
                        "created_at": "2024-01-01T00:00:00Z"
                    }
                ]
            }

    client = TwitchAPIClient(auth_provider=DummyAuth(), client_id="test_client_id")
    monkeypatch.setattr(client.session, "get", lambda url, headers, timeout: DummyResponse())

    user_data = client.fetch_user_data()
    assert user_data["username"] == "streamer_twitch"
    assert user_data["display_name"] == "StreamerTwitch"
    assert user_data["broadcaster_id"] == "99999"
    assert user_data["platform"] == "twitch"

def test_route_incoming_message_dto():
    from backend.services.chat.pipeline import ChatMessageDTO
    from backend.core.main_window_core import MainWindowCore

    class DummyChatController:
        def __init__(self):
            self.last_dto = None
        def process_message(self, dto):
            self.last_dto = dto

    mw = MainWindowCore.__new__(MainWindowCore)
    mw.chat_controller = DummyChatController()
    mw._metrics = {}
    mw._increment_metric = lambda key: None

    dto = ChatMessageDTO(user="TwitchUser", content="Hola Twitch!", badges=[], color="#9146FF", msg_id="123", sender_id=999, platform="twitch")
    mw._route_incoming_message(dto)
    assert mw.chat_controller.last_dto.user == "TwitchUser"
    assert mw.chat_controller.last_dto.platform == "twitch"

def test_twitch_emote_parsing_and_stripping():
    emotes_tag = "emotesv2_a04b827d1e9043e7b11ce01c59be26f0:0-17,19-36"
    assert TwitchSocketManager.count_twitch_emotes(emotes_tag) == 2

    raw_text = "theand96Happyhappy theand96Happyhappy"
    clean_text = TwitchSocketManager.strip_twitch_emotes(raw_text, emotes_tag)
    assert clean_text == ""

    single_tag = "25:0-4"
    text_with_words = "Kappa es un emote famoso"
    clean_words = TwitchSocketManager.strip_twitch_emotes(text_with_words, single_tag)
    assert clean_words == "es un emote famoso"

def test_clean_message_for_tts_twitch_emotes():
    from backend.handlers.chat_filter_handler import ChatFilterHandler
    handler = ChatFilterHandler(i18n=None, service=None)
    emotes_tag = "emotesv2_a04b827d1e9043e7b11ce01c59be26f0:0-17,19-36"
    raw_text = "theand96Happyhappy theand96Happyhappy"
    cleaned = handler.clean_message_for_tts(raw_text, emotes_tag=emotes_tag)
    assert cleaned == ""

    text_with_msg = "Hola streamer theand96Happyhappy"
    tag2 = "emotesv2_a04b827d1e9043e7b11ce01c59be26f0:14-31"
    cleaned2 = handler.clean_message_for_tts(text_with_msg, emotes_tag=tag2)
    assert cleaned2 == "Hola streamer"
