# resources\tests\test_json_utils.py

import io
from backend.utils.json_utils import fast_loads, fast_dumps, fast_load, fast_dump, parse_kick_payload, BACKEND_ENGINE


def test_json_engine_is_optimized():
    assert BACKEND_ENGINE in ("msgspec", "orjson", "json")

def test_fast_loads_and_fast_dumps():
    data = {
        "channel": "theandro2k",
        "count": 42,
        "is_live": True,
        "tags": ["streamer", "gaming"],
        "nested": {"score": 99.5}
    }
    serialized = fast_dumps(data)
    assert isinstance(serialized, str)
    deserialized = fast_loads(serialized)
    assert deserialized == data

    assert fast_loads(serialized.encode("utf-8")) == data
    assert fast_loads(bytearray(serialized.encode("utf-8"))) == data

def test_fast_dumps_with_indent():
    data = {"name": "MiniKick", "version": "1.6.1"}
    indented = fast_dumps(data, indent=2)
    assert "\n" in indented
    assert '"name"' in indented
    assert fast_loads(indented) == data

def test_fast_load_and_dump_streams():
    data = {"status": "ok", "items": [1, 2, 3]}
    stream = io.StringIO()
    fast_dump(data, stream, indent=4)
    stream.seek(0)
    loaded = fast_load(stream)
    assert loaded == data

def test_parse_kick_payload():
    assert parse_kick_payload("") == ("", {})
    assert parse_kick_payload(None) == ("", {})

    inner_json = fast_dumps({"user": "viewer1", "content": "hola"})
    raw_event = fast_dumps({"event": "ChatMessageEvent", "data": inner_json})
    event, data = parse_kick_payload(raw_event)
    assert event == "ChatMessageEvent"
    assert data["user"] == "viewer1"
    assert data["content"] == "hola"

    raw_empty_data = fast_dumps({"event": "subscription_succeeded", "data": "{}"})
    event, data = parse_kick_payload(raw_empty_data)
    assert event == "subscription_succeeded"
    assert data == {}
