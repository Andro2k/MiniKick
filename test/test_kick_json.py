import json
import websocket

# Credenciales públicas de Pusher para Kick
CLUSTER = "us2"
KEY = "32cbd69e4b950bf97679"

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
        # Extraemos el payload interno del mensaje
        payload = json.loads(data.get("data", "{}"))
        
        print("\n" + "═"*60)
        print("📥 NUEVO MENSAJE DETECTADO (JSON CRUDO)")
        print("═"*60)
        
        # Imprimimos todo el JSON formateado de forma bonita (indent=4)
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

if __name__ == "__main__":
    print("=================================================")
    print("   🔍 PROTOTIPO: INSPECTOR DE JSON DE KICK 🔍   ")
    print("=================================================")
    
    # Pide el ID de la sala (puedes verlo en el Dashboard de MiniKick)
    ROOM_ID = input("Ingresa el ID de tu sala (Míralo en tu Dashboard): ").strip()

    url = f"wss://ws-{CLUSTER}.pusher.com/app/{KEY}?protocol=7&client=js&version=7.6.0"
    
    ws = websocket.WebSocketApp(url,
                                on_open=on_open,
                                on_message=on_message,
                                on_error=on_error,
                                on_close=on_close)

    print("\n[+] Iniciando escucha. Escribe algo en tu chat de Kick para ver la magia...")
    ws.run_forever(ping_interval=30, ping_timeout=10)