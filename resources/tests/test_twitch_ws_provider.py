# resources\tests\test_twitch_ws_provider.py

from backend.providers.chat.twitch_ws_provider import TwitchSocketManager


def test_strip_twitch_emotes_single_and_multiple():
    assert TwitchSocketManager.strip_twitch_emotes("Hello Kappa world", "25:6-10") == "Hello world"
    assert TwitchSocketManager.strip_twitch_emotes(
        "Kappa PogChamp LUL", "25:0-4/88:6-13/425618:15-17"
    ) == ""
    assert TwitchSocketManager.strip_twitch_emotes(
        "PogChamp test message Kappa", "88:0-7/25:22-26"
    ) == "test message"

def test_strip_twitch_emotes_empty_inputs():
    assert TwitchSocketManager.strip_twitch_emotes("", "25:0-4") == ""
    assert TwitchSocketManager.strip_twitch_emotes("Hello", "") == "Hello"

def test_count_twitch_emotes():
    assert TwitchSocketManager.count_twitch_emotes("25:0-4,6-10/88:12-19") == 3
    assert TwitchSocketManager.count_twitch_emotes("25:6-10") == 1
    assert TwitchSocketManager.count_twitch_emotes("") == 0

def test_parse_privmsg_invokes_callback():
    manager = TwitchSocketManager()
    received = []
    manager._callback = (
        lambda user, content, badges, color, msg_id, sender_id, emotes_tag="", gif_url="":
        received.append((user, content, color, msg_id))
    )
    manager._running = True

    raw_privmsg = (
        "@id=msg_123;display-name=Tester;user-id=1001;color=#FF0000 "
        ":tester!tester@tmi.twitch.tv PRIVMSG #mychan :Hello World"
    )
    manager._parse_privmsg(raw_privmsg)

    assert received == [("Tester", "Hello World", "#FF0000", "msg_123")]
