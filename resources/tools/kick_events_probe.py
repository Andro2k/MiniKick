# resources\tools\kick_events_probe.py

import argparse
import json
import os
import sys
import time
from typing import Any, Callable, Dict, List, Optional, Tuple

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

import websocket

from backend.config import KICK_CHANNEL_URL, KICK_PUSHER
from resources.tools.pusher_probe import PUSHER_URL, probe_key

DEFAULT_DURATION_S = 600
_RECV_TIMEOUT_S = 2
_SAMPLE_CHARS = 240
_CHAT_EVENT_MARKERS = ("ChatMessageEvent",)
_BASE_CHANNELS = (
    "chatrooms.{room}.v2",
    "chatroom_{room}",
    "channel_{channel}",
    "channel.{channel}",
)
_TYPE_HINTS = (
    ("gift", "sub_gift"),
    ("subscri", "subscription"),
    ("follow", "follow"),
    ("raid", "raid"),
    ("host", "raid"),
    ("kicks", "cheer"),
    ("reward", "reward"),
)


def build_channels(room: Optional[str], channel: Optional[str], extra: Tuple[str, ...] = ()) -> List[str]:
    values = {"room": room, "channel": channel}
    channels: List[str] = []
    for template in (*_BASE_CHANNELS, *extra):
        needed = [name for name in values if "{" + name + "}" in template]
        if any(not values[name] for name in needed):
            continue
        name = template.format(**values)
        if name not in channels:
            channels.append(name)
    return channels


def parse_data(data: Any) -> Any:
    if isinstance(data, (dict, list)):
        return data
    try:
        return json.loads(data)
    except (TypeError, ValueError):
        return data


def shape(value: Any, depth: int = 2) -> Any:
    if isinstance(value, dict):
        if depth <= 0:
            return "object"
        return {key: shape(item, depth - 1) for key, item in value.items()}
    if isinstance(value, list):
        return [shape(value[0], depth - 1)] if value and depth > 0 else "list"
    return type(value).__name__


def suggest_type(event_name: str) -> Optional[str]:
    lowered = event_name.lower()
    return next((kind for marker, kind in _TYPE_HINTS if marker in lowered), None)


class EventCatalog:
    def __init__(self) -> None:
        self.subscriptions: Dict[str, str] = {}
        self.events: Dict[Tuple[str, str], Dict[str, Any]] = {}
        self.chat_frames_ignored = 0

    def record_subscription(self, channel: str, status: str) -> None:
        self.subscriptions[channel] = status

    def record_event(self, channel: str, event: str, payload: Any, elapsed_s: float) -> bool:
        key = (channel, event)
        entry = self.events.get(key)
        if entry is not None:
            entry["count"] += 1
            return False
        self.events[key] = {
            "channel": channel,
            "event": event,
            "count": 1,
            "first_seen_s": round(elapsed_s, 1),
            "shape": shape(payload),
            "sample": json.dumps(payload, ensure_ascii=False, default=str)[:_SAMPLE_CHARS],
            "possible_type": suggest_type(event),
        }
        return True

    def report(self) -> Dict[str, Any]:
        return {
            "subscriptions": dict(self.subscriptions),
            "events": sorted(self.events.values(), key=lambda e: (e["channel"], e["event"])),
            "chat_frames_ignored": self.chat_frames_ignored,
        }


def _classify(event: str) -> str:
    if event in ("pusher_internal:subscription_succeeded", "pusher:subscription_succeeded"):
        return "subscribed"
    if event in ("pusher:subscription_error", "pusher_internal:subscription_error", "pusher:error"):
        return "error"
    return "event"


def listen(
    cluster: str,
    key: str,
    channels: List[str],
    duration: int,
    include_chat: bool = False,
    ws_factory: Optional[Callable] = None,
    clock: Callable[[], float] = time.monotonic,
    on_new_event: Optional[Callable[[Dict[str, Any]], None]] = None,
) -> Dict[str, Any]:
    catalog = EventCatalog()
    note = ""
    ws = (ws_factory or websocket.create_connection)(PUSHER_URL.format(cluster=cluster, key=key), timeout=10)
    try:
        for channel in channels:
            ws.send(json.dumps({"event": "pusher:subscribe", "data": {"channel": channel}}))
            catalog.record_subscription(channel, "pending")
        started = clock()
        ws.settimeout(_RECV_TIMEOUT_S)
        while clock() - started < duration:
            try:
                raw = ws.recv()
            except websocket.WebSocketTimeoutException:
                continue
            except Exception as exc:
                note = f"socket cerrado: {type(exc).__name__}"
                break
            frame = parse_data(raw) if raw else {}
            if not isinstance(frame, dict):
                continue
            event = str(frame.get("event", "?"))
            channel = str(frame.get("channel", ""))
            if event == "pusher:ping":
                ws.send(json.dumps({"event": "pusher:pong", "data": {}}))
                continue
            kind = _classify(event)
            if kind == "subscribed":
                catalog.record_subscription(channel, "ok")
            elif kind == "error":
                payload = parse_data(frame.get("data"))
                catalog.record_subscription(channel or "?", f"error: {str(payload)[:120]}")
            elif event.startswith("pusher:"):
                continue
            elif not include_chat and any(marker in event for marker in _CHAT_EVENT_MARKERS):
                catalog.chat_frames_ignored += 1
            elif catalog.record_event(channel, event, parse_data(frame.get("data")), clock() - started) and on_new_event:
                on_new_event(catalog.events[(channel, event)])
    except KeyboardInterrupt:
        note = "interrumpido por el usuario"
    finally:
        try:
            ws.close()
        except Exception:
            pass
    result = catalog.report()
    result["note"] = note
    return result


def resolve_ids(slug: str) -> Tuple[Optional[str], Optional[str], str]:
    from backend.providers.chat.kick_provider import ScraperFactory
    try:
        response = ScraperFactory.create().get(KICK_CHANNEL_URL.format(slug=slug), timeout=10)
        if response.status_code != 200:
            return None, None, f"HTTP {response.status_code}"
        data = response.json()
    except Exception as exc:
        return None, None, f"{type(exc).__name__}: {exc}"
    channel = data.get("id") or (data.get("chatroom") or {}).get("channel_id")
    room = (data.get("chatroom") or {}).get("id")
    return (str(channel) if channel else None), (str(room) if room else None), ""


def _print_live(entry: Dict[str, Any]) -> None:
    hint = f"  -> posible: {entry['possible_type']}" if entry["possible_type"] else ""
    print(f"[{entry['first_seen_s']:>6}s] {entry['channel']}  {entry['event']}  claves={list(entry['shape']) if isinstance(entry['shape'], dict) else entry['shape']}{hint}", flush=True)


def _print_summary(result: Dict[str, Any]) -> None:
    print("\nSuscripciones:")
    for channel, status in result["subscriptions"].items():
        print(f"  {'OK ' if status == 'ok' else '-- '} {channel}: {status}")
    print(f"\nEventos distintos (sin chat): {len(result['events'])} | frames de chat ignorados: {result['chat_frames_ignored']}")
    for entry in result["events"]:
        hint = f" | posible: {entry['possible_type']}" if entry["possible_type"] else ""
        print(f"  {entry['channel']}  {entry['event']}  x{entry['count']}{hint}")
    if result.get("note"):
        print(f"Aviso: {result['note']}")


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description="MiniKick - catálogo de eventos realtime de Kick (follows, subs, regalos...)")
    parser.add_argument("--slug", help="Usuario del canal; resuelve channel-id y room automáticamente")
    parser.add_argument("--channel-id", help="ID del canal (para channel_{id} y channel.{id})")
    parser.add_argument("--room", help="ID del chatroom (para chatrooms.{room}.v2 y chatroom_{room})")
    parser.add_argument("--extra-channel", action="append", default=[], help="Canal adicional a probar; admite {room} y {channel}")
    parser.add_argument("--duration", type=int, default=DEFAULT_DURATION_S, help="Segundos a escuchar (Ctrl+C para terminar antes)")
    parser.add_argument("--include-chat", action="store_true", help="Incluir los mensajes de chat en el catálogo")
    parser.add_argument("--out", help="Guardar el reporte completo (con muestras) en este archivo JSON")
    args = parser.parse_args(argv)

    channel_id, room = args.channel_id, args.room
    if args.slug and not (channel_id and room):
        found_channel, found_room, error = resolve_ids(args.slug)
        if error:
            print(f"No se pudo resolver '{args.slug}': {error}. Pasa --channel-id y --room a mano.")
            return 1
        channel_id, room = channel_id or found_channel, room or found_room
    channels = build_channels(room, channel_id, tuple(args.extra_channel))
    if not channels:
        print("Indica --slug, o --channel-id y/o --room.")
        return 1

    key = next((k for k in KICK_PUSHER.keys if probe_key(KICK_PUSHER.cluster, k)[0]), None)
    if key is None:
        print("Ninguna clave de Pusher fue aceptada.")
        return 1

    print(f"Canal={channel_id} room={room} | escuchando {args.duration}s en {len(channels)} canales. Genera un follow/sub/regalo de prueba.")
    result = listen(KICK_PUSHER.cluster, key, channels, args.duration, args.include_chat, on_new_event=_print_live)
    _print_summary(result)
    if args.out:
        with open(args.out, "w", encoding="utf-8") as handle:
            json.dump(result, handle, indent=2, ensure_ascii=False)
        print(f"Reporte guardado en {args.out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
