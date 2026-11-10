# resources\tools\pusher_probe.py

import argparse
import json
import os
import sys
import time
import uuid
from collections import Counter
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

import requests
import websocket

from backend.config import KICK_PUSHER

PUSHER_URL = "wss://ws-{cluster}.pusher.com/app/{key}?protocol=7&client=js&version=7.6.0"
DEFAULT_TIMEOUT = 10
KICK_ORIGIN = "https://kick.com"
REALTIME_CONNECTION_URL = "https://web.kick.com/api/v1/realtime/channels/{channel_id}/chat/connection"


def _parse_data(data) -> dict:
    if isinstance(data, dict):
        return data
    try:
        parsed = json.loads(data)
        return parsed if isinstance(parsed, dict) else {}
    except (TypeError, ValueError):
        return {}


def probe_key(cluster: str, key: str, timeout: int = DEFAULT_TIMEOUT) -> Tuple[bool, str]:
    try:
        ws = websocket.create_connection(PUSHER_URL.format(cluster=cluster, key=key), timeout=timeout)
    except Exception as exc:
        return False, f"no se pudo conectar: {exc}"
    try:
        frame = json.loads(ws.recv())
    except Exception as exc:
        return False, f"sin respuesta válida: {exc}"
    finally:
        try:
            ws.close()
        except Exception:
            pass

    event = frame.get("event") if isinstance(frame, dict) else None
    if event == "pusher:connection_established":
        return True, "aceptada (pusher:connection_established)"
    if event == "pusher:error":
        data = _parse_data(frame.get("data"))
        return False, f"rechazada (pusher:error code={data.get('code')}: {data.get('message')})"
    return False, f"respuesta inesperada: {event}"


def discover_transports(channel_id: int, timeout: int = DEFAULT_TIMEOUT) -> Tuple[List[Dict[str, Any]], str]:
    body = {
        "client": {"id": str(uuid.uuid4()), "type": "web"},
        "capabilities": {"accepted_providers": [{"provider": "centrifugo"}, {"provider": "pusher"}]},
    }
    headers = {"Origin": KICK_ORIGIN, "Referer": KICK_ORIGIN + "/", "User-Agent": "Mozilla/5.0"}
    try:
        resp = requests.post(REALTIME_CONNECTION_URL.format(channel_id=channel_id), json=body, headers=headers, timeout=timeout)
    except Exception as exc:
        return [], f"no se pudo consultar: {exc}"
    if resp.status_code != 200:
        return [], f"HTTP {resp.status_code}"
    try:
        items = (resp.json().get("data") or {}).get("connections") or []
    except ValueError:
        return [], "respuesta no es JSON"

    providers = []
    for item in items:
        creds = item.get("credentials") or {}
        entry = {"provider": item.get("provider"), "url": creds.get("url"), "cluster": creds.get("cluster"),
                 "key_preview": f"{creds['app_key'][:4]}…{creds['app_key'][-4:]}" if creds.get("app_key") else None}
        if entry["url"]:
            entry["handshake"] = check_handshake(entry["url"], timeout)
        providers.append(entry)
    return providers, ""


def check_handshake(url: str, timeout: int = DEFAULT_TIMEOUT) -> str:
    started = time.monotonic()
    try:
        ws = websocket.create_connection(url, timeout=timeout, origin=KICK_ORIGIN)
    except websocket.WebSocketBadStatusException as exc:
        return f"rechazado (HTTP {exc.status_code})"
    except Exception as exc:
        return f"falló: {exc}"
    try:
        ws.close()
    except Exception:
        pass
    return f"ok ({time.monotonic() - started:.2f}s)"


def _transit_seconds(created_at) -> Optional[float]:
    if not isinstance(created_at, str):
        return None
    try:
        created = datetime.fromisoformat(created_at.replace("Z", "+00:00"))
    except ValueError:
        return None
    if created.tzinfo is None:
        created = created.replace(tzinfo=timezone.utc)
    return (datetime.now(timezone.utc) - created).total_seconds()


def listen_stats(cluster: str, key: str, room: str, wait: int, ws_factory=None, on_frame=None) -> Dict[str, Any]:
    ws = (ws_factory or websocket.create_connection)(PUSHER_URL.format(cluster=cluster, key=key), timeout=DEFAULT_TIMEOUT)
    events: Counter = Counter()
    gaps: List[float] = []
    transit: List[float] = []
    reconnect_hint = None
    try:
        ws.send(json.dumps({"event": "pusher:subscribe", "data": {"channel": f"chatrooms.{room}.v2"}}))
        started = last = time.monotonic()
        ws.settimeout(2)
        while time.monotonic() - started < wait:
            try:
                raw = ws.recv()
            except websocket.WebSocketTimeoutException:
                continue
            except Exception as exc:
                reconnect_hint = f"socket cerrado tras {time.monotonic() - started:.1f}s: {exc}"
                break
            now = time.monotonic()
            gaps.append(now - last)
            last = now
            frame = json.loads(raw) if raw else {}
            event = frame.get("event", "?") if isinstance(frame, dict) else "?"
            events[event] += 1
            if on_frame:
                on_frame(event, now - started)
            if event == "pusher:ping":
                ws.send(json.dumps({"event": "pusher:pong", "data": {}}))
                continue
            inner = _parse_data(frame.get("data")) if isinstance(frame, dict) else {}
            latency = _transit_seconds(inner.get("created_at"))
            if latency is not None:
                transit.append(latency)
    finally:
        try:
            ws.close()
        except Exception:
            pass

    def _avg(values): return round(sum(values) / len(values), 3) if values else None
    return {
        "seconds": wait, "frames": sum(events.values()), "events": dict(events),
        "max_gap_s": round(max(gaps), 2) if gaps else None,
        "chat_messages": len(transit), "transit_avg_s": _avg(transit),
        "transit_max_s": round(max(transit), 2) if transit else None,
        "transit_over_5s": sum(1 for v in transit if v > 5), "note": reconnect_hint,
    }


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description="MiniKick - Kick realtime probe")
    parser.add_argument("--idle", "--listen", action="store_true", dest="idle", help="Suscribe a un chat y resume los frames recibidos (responde pusher:ping)")
    parser.add_argument("--room", default="89137556", help="ID del chatroom para --idle")
    parser.add_argument("--wait", type=int, default=130, help="Segundos a escuchar en --idle")
    parser.add_argument("--discover", action="store_true", help="Pregunta a Kick qué transportes realtime ofrece (Pusher/Centrifugo) y prueba el handshake")
    parser.add_argument("--channel-id", type=int, default=None, help="ID de canal para --discover")
    parser.add_argument("--json", action="store_true", help="Salida en formato JSON")
    args = parser.parse_args(argv)

    results = []
    for index, key in enumerate(KICK_PUSHER.keys, 1):
        accepted, detail = probe_key(KICK_PUSHER.cluster, key)
        results.append({"index": index, "key_preview": f"{key[:4]}…{key[-4:]}", "accepted": accepted, "detail": detail})

    discovery = None
    if args.discover:
        if args.channel_id is None:
            print("--discover necesita --channel-id")
        else:
            providers, error = discover_transports(args.channel_id)
            discovery = {"channel_id": args.channel_id, "providers": providers, "error": error}

    stats = None
    if args.idle:
        usable = next((k for k, r in zip(KICK_PUSHER.keys, results) if r["accepted"]), None)
        if usable is not None:
            stats = listen_stats(KICK_PUSHER.cluster, usable, args.room, args.wait)

    if args.json:
        print(json.dumps({"cluster": KICK_PUSHER.cluster, "results": results, "discovery": discovery, "listen": stats},
                         indent=2, ensure_ascii=False))
    else:
        print(f"Cluster: {KICK_PUSHER.cluster}")
        for r in results:
            icon = "✅" if r["accepted"] else "❌"
            tag = " (preferida)" if r["index"] == 1 else ""
            print(f"  {icon} clave {r['index']}/{len(results)}{tag} {r['key_preview']}: {r['detail']}")
        if discovery:
            if discovery["error"]:
                print(f"Transportes ofrecidos por Kick: error ({discovery['error']})")
            else:
                print("Transportes ofrecidos por Kick (en orden de preferencia):")
                for p in discovery["providers"]:
                    extra = p.get("url") or (f"cluster={p.get('cluster')} clave={p.get('key_preview')}")
                    print(f"  - {p['provider']}: {extra}" + (f" | handshake: {p['handshake']}" if p.get("handshake") else ""))
        if args.idle:
            if stats is None:
                print("No hay ninguna clave aceptada: no se puede escuchar el chat.")
            else:
                print(f"Escucha {stats['seconds']}s: {stats['frames']} frames, eventos={stats['events']}")
                print(f"  mayor silencio: {stats['max_gap_s']}s | mensajes de chat: {stats['chat_messages']}"
                      f" | latencia created_at→recibido avg={stats['transit_avg_s']}s max={stats['transit_max_s']}s"
                      f" | >5s: {stats['transit_over_5s']}")
                if stats["note"]:
                    print(f"  aviso: {stats['note']}")

    return 0 if results and results[0]["accepted"] else 1


if __name__ == "__main__":
    sys.exit(main())
