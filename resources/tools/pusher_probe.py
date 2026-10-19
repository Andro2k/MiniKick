# resources/tools/pusher_probe.py
"""
MiniKick - Pusher Key Probe
===========================
Comprueba contra el servidor REAL de Pusher qué claves de KICK_PUSHER acepta Kick en este momento,
y (opcionalmente) escucha frames de un chat. Sustituye al antiguo test_pusher_idle.py, que abría una
conexión de red al importarse y bloqueaba la ejecución de pytest.

Uso:
  python resources/tools/pusher_probe.py                                  (prueba todas las claves configuradas)
  python resources/tools/pusher_probe.py --idle --room 89137556 --wait 130 (suscribe y espera frames)
  python resources/tools/pusher_probe.py --json                            (salida máquina)

Código de salida: 0 si la clave PREFERIDA (la primera de KICK_PUSHER.keys) fue aceptada, 1 si no.
"""

import argparse
import json
import os
import sys
import time
from typing import Optional, Tuple

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

import websocket

from backend.config import KICK_PUSHER

PUSHER_URL = "wss://ws-{cluster}.pusher.com/app/{key}?protocol=7&client=js&version=7.6.0"
DEFAULT_TIMEOUT = 10


def _parse_data(data) -> dict:
    if isinstance(data, dict):
        return data
    try:
        parsed = json.loads(data)
        return parsed if isinstance(parsed, dict) else {}
    except (TypeError, ValueError):
        return {}


def probe_key(cluster: str, key: str, timeout: int = DEFAULT_TIMEOUT) -> Tuple[bool, str]:
    """Abre una conexión con la clave y lee el primer frame. Devuelve (aceptada, detalle)."""
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


def listen_idle(cluster: str, key: str, room: str, wait: int) -> Optional[str]:
    """Suscribe al chat y espera hasta 'wait' segundos un frame. Devuelve el frame o None."""
    ws = websocket.create_connection(PUSHER_URL.format(cluster=cluster, key=key), timeout=DEFAULT_TIMEOUT)
    try:
        print("Established:", ws.recv())
        ws.send(json.dumps({"event": "pusher:subscribe", "data": {"channel": f"chatrooms.{room}.v2"}}))
        print("Subscribed:", ws.recv())
        print(f"Esperando frames (hasta {wait}s)...")
        ws.settimeout(wait)
        start = time.time()
        try:
            msg = ws.recv()
            print(f"Recibido a los {time.time() - start:.1f}s:", msg)
            return msg
        except Exception as exc:
            print(f"Sin frames tras {time.time() - start:.1f}s: {exc}")
            return None
    finally:
        ws.close()


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description="MiniKick - Pusher Key Probe")
    parser.add_argument("--idle", action="store_true", help="Tras probar las claves, suscribe a un chat y espera frames")
    parser.add_argument("--room", default="89137556", help="ID del chatroom para --idle")
    parser.add_argument("--wait", type=int, default=130, help="Segundos a esperar frames en --idle")
    parser.add_argument("--json", action="store_true", help="Salida en formato JSON")
    args = parser.parse_args(argv)

    results = []
    for index, key in enumerate(KICK_PUSHER.keys, 1):
        accepted, detail = probe_key(KICK_PUSHER.cluster, key)
        results.append({"index": index, "key_preview": f"{key[:4]}…{key[-4:]}", "accepted": accepted, "detail": detail})

    if args.json:
        print(json.dumps({"cluster": KICK_PUSHER.cluster, "results": results}, indent=2, ensure_ascii=False))
    else:
        print(f"Cluster: {KICK_PUSHER.cluster}")
        for r in results:
            icon = "✅" if r["accepted"] else "❌"
            tag = " (preferida)" if r["index"] == 1 else ""
            print(f"  {icon} clave {r['index']}/{len(results)}{tag} {r['key_preview']}: {r['detail']}")

    if args.idle:
        usable = next((k for k, r in zip(KICK_PUSHER.keys, results) if r["accepted"]), None)
        if usable is None:
            print("No hay ninguna clave aceptada: no se puede escuchar el chat.")
        else:
            listen_idle(KICK_PUSHER.cluster, usable, args.room, args.wait)

    return 0 if results and results[0]["accepted"] else 1


if __name__ == "__main__":
    sys.exit(main())
