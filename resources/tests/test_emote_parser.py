from backend.utils.emote_parser import extract_emotes


def test_extracts_kick_image_and_text_emotes():
    emotes = extract_emotes("hi [emote:123:KEKW] [emote:LUL]", "kick")
    assert emotes == [
        {"type": "image", "src": "https://files.kick.com/emotes/123/fullsize", "name": "KEKW"},
        {"type": "text", "src": "LUL", "name": "LUL"},
    ]


def test_extracts_unicode_emojis():
    emotes = extract_emotes("gg 🔥", "kick")
    assert emotes == [{"type": "text", "src": "🔥", "name": "🔥"}]


def test_extracts_twitch_tag_emotes():
    emotes = extract_emotes("Kappa", "twitch", "25:0-4/1902:6-10")
    assert [e["name"] for e in emotes] == ["twitch_25", "twitch_1902"]
    assert emotes[0]["src"].endswith("/25/default/dark/2.0")


def test_extracts_youtube_json_emotes_and_ignores_invalid_payload():
    tag = '[{"url": "http://x/e.png", "name": "wow"}, {"name": "nourl"}]'
    assert extract_emotes("x", "youtube", tag) == [
        {"type": "image", "src": "http://x/e.png", "name": "wow"}
    ]
    assert extract_emotes("x", "tiktok", "[not json") == []


def test_plain_message_has_no_emotes():
    assert extract_emotes("hola mundo", "kick") == []
