import json
import websocket
import requests
import sys
import os
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(current_dir)
if project_root not in sys.path:
    sys.path.append(project_root)

from backend.config.api_keys import KICK_CLIENT_ID, KICK_CLIENT_SECRET
CLUSTER = "us2"
KEY = "32cbd69e4b950bf97679"
ROOM_ID = "30913450"

def on_message(ws, message):
    data = json.loads(message)
    event = data.get("event")

    if event == "pusher:connection_established":
        print("[+] Conexión establecida con éxito. Suscribiéndose al chat...")
        ws.send(json.dumps({
            "event": "pusher:subscribe",
            "data": {"channel": f"chatrooms.{ROOM_ID}.v2"}
        }))

    elif event == "App\\Events\\ChatMessageEvent":
        payload = json.loads(data.get("data", "{}"))
        
        print("\n" + "═"*60)
        print("NUEVO MENSAJE DETECTADO (JSON CRUDO)")
        print("═"*60)
        print(json.dumps(payload, indent=4, ensure_ascii=False))
        print("═"*60 + "\n")

    elif event == "pusher:ping":
        ws.send(json.dumps({"event": "pusher:pong"}))

def on_error(ws, error):
    print(f"[!] Error de conexión: {error}")

def on_close(ws, close_status_code, close_msg):
    print("[-] Conexión cerrada.")

def on_open(ws):
    print("[+] Abriendo socket con los servidores de Kick...")

def get_access_token():
    print("[+] Obteniendo App Access Token de Kick...")
    url = "https://id.kick.com/oauth/token"
    data = {
        "grant_type": "client_credentials",
        "client_id": KICK_CLIENT_ID,
        "client_secret": KICK_CLIENT_SECRET
    }
    response = requests.post(url, data=data)
    if response.status_code == 200:
        token = response.json().get("access_token")
        print("[+] Token obtenido exitosamente.")
        return token
    else:
        print(f"[!] Error al obtener token: {response.status_code} {response.text}")
        return None

def test_get_livestreams_v2():
    token = get_access_token()
    if not token: return
    
    url = "https://api.kick.com/public/v2/livestreams"
    print(f"\n[+] Realizando petición GET a {url}")
    headers = {"Authorization": f"Bearer {token}"}
    params = {"limit": 5}
    response = requests.get(url, headers=headers, params=params)
    if response.status_code == 200:
        print(json.dumps(response.json(), indent=4, ensure_ascii=False))
    else:
        print(f"[!] Error {response.status_code}: {response.text}")

def test_get_livestreams_v1():
    token = get_access_token()
    if not token: return

    url = "https://api.kick.com/public/v1/livestreams"
    print(f"\n[+] Realizando petición GET a {url} (Deprecated)")
    headers = {"Authorization": f"Bearer {token}"}
    params = {"limit": 5}
    response = requests.get(url, headers=headers, params=params)
    if response.status_code == 200:
        print(json.dumps(response.json(), indent=4, ensure_ascii=False))
    else:
        print(f"[!] Error {response.status_code}: {response.text}")

def test_get_livestreams_stats():
    token = get_access_token()
    if not token: return

    url = "https://api.kick.com/public/v1/livestreams/stats"
    print(f"\n[+] Realizando petición GET a {url}")
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        print(json.dumps(response.json(), indent=4, ensure_ascii=False))
    else:
        print(f"[!] Error {response.status_code}: {response.text}")

if __name__ == "__main__":
    print("=================================================")
    print("   🔍 PROTOTIPO: INSPECTOR DE JSON DE KICK 🔍   ")
    print("=================================================")
    print("1. Escuchar Chat via WebSockets")
    print("2. Test Get Livestreams (v2)")
    print("3. Test Get Livestreams (v1) [Deprecated]")
    print("4. Test Get Livestreams Stats (v1)")
    opcion = input("\nElige una opción (1-4): ").strip()

    if opcion == "1":
        ROOM_ID = input("Ingresa el ID de tu sala (Míralo en tu Dashboard): ").strip()
        url = f"wss://ws-{CLUSTER}.pusher.com/app/{KEY}?protocol=7&client=js&version=7.6.0"
        ws = websocket.WebSocketApp(url,
                                    on_open=on_open,
                                    on_message=on_message,
                                    on_error=on_error,
                                    on_close=on_close)

        print("\n[+] Iniciando escucha. Escribe algo en tu chat de Kick para ver la magia...")
        ws.run_forever(ping_interval=30, ping_timeout=10)
    elif opcion == "2":
        test_get_livestreams_v2()
    elif opcion == "3":
        test_get_livestreams_v1()
    elif opcion == "4":
        test_get_livestreams_stats()
    else:
        print("Opción no válida.")