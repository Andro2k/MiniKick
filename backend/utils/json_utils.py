# backend\utils\json_utils.py

import logging
from typing import Any

logger = logging.getLogger("minikick.utils.json")

BACKEND_ENGINE: str = "json"
try:
    import msgspec
    _decoder = msgspec.json.Decoder()
    _encoder = msgspec.json.Encoder()

    def fast_loads(payload: str | bytes | bytearray) -> Any:
        if isinstance(payload, str):
            return _decoder.decode(payload.encode("utf-8"))
        return _decoder.decode(payload)

    def fast_dumps(obj: Any) -> str:
        return _encoder.encode(obj).decode("utf-8")

    BACKEND_ENGINE = "msgspec"

except ImportError:
    try:
        import orjson

        def fast_loads(payload: str | bytes | bytearray) -> Any:
            if isinstance(payload, str):
                return orjson.loads(payload.encode("utf-8"))
            return orjson.loads(payload)

        def fast_dumps(obj: Any) -> str:
            return orjson.dumps(obj).decode("utf-8")

        BACKEND_ENGINE = "orjson"

    except ImportError:
        import json

        def fast_loads(payload: str | bytes | bytearray) -> Any:
            return json.loads(payload)

        def fast_dumps(obj: Any) -> str:
            return json.dumps(obj, ensure_ascii=False)

        BACKEND_ENGINE = "json"

logger.debug("[JsonUtils] Fast JSON parser initialized with engine: %s", BACKEND_ENGINE)

def parse_kick_payload(raw: str | bytes | bytearray) -> tuple[str, dict]:
    if not raw:
        return "", {}

    try:
        outer = fast_loads(raw)
        if not isinstance(outer, dict):
            return "", {}

        event = outer.get("event", "")
        data_raw = outer.get("data", {})

        if isinstance(data_raw, (str, bytes, bytearray)):
            if not data_raw or data_raw == "{}" or data_raw == "[]":
                inner_data = {}
            else:
                inner_data = fast_loads(data_raw)
                if not isinstance(inner_data, dict):
                    inner_data = {}
        elif isinstance(data_raw, dict):
            inner_data = data_raw
        else:
            inner_data = {}

        return str(event), inner_data

    except Exception:
        return "", {}
