import os
import json
import websocket
from dotenv import load_dotenv
from curl_cffi import requests as cffi_requests

# Cargar las variables del archivo .env
load_dotenv()
PUSHER_KEY = os.getenv("KICK_PUSHER_KEY")
PUSHER_CLUSTER = os.getenv("KICK_PUSHER_CLUSTER", "us2")

def obtener_chatroom_id(streamer):
    """
    Técnica de Scraping de API Interna: Engaña a Cloudflare 
    simulando ser Chrome para extraer el JSON limpio.
    """
    print(f"[*] Buscando Chatroom ID para el canal: {streamer}...")
    url = f"https://kick.com/api/v1/channels/{streamer}"
    
    try:
        # impersonate="chrome124" es la magia que burla el Error 403
        response = cffi_requests.get(url, impersonate="chrome124", timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            chatroom_id = data.get("chatroom", {}).get("id")
            
            if chatroom_id:
                print(f"[+] Éxito: Chatroom ID encontrado -> {chatroom_id}")
                return chatroom_id
            else:
                print("[-] Error: El JSON no contiene un chatroom ID válido.")
        else:
            print(f"[-] Error HTTP {response.status_code}: Cloudflare bloqueó la petición o el canal no existe.")
    except Exception as e:
        print(f"[-] Error de conexión: {e}")
        
    return None

# ==========================================
# EVENTOS DEL WEBSOCKET PUSHER
# ==========================================
def on_message(ws, message):
    """Procesa los mensajes en tiempo real que llegan desde Kick"""
    try:
        data = json.loads(message)
        evento = data.get("event")
        
        # --- NUEVO: Responder al latido del servidor para evitar desconexiones ---
        if evento == "pusher:ping":
            ws.send(json.dumps({"event": "pusher:pong", "data": {}}))
            return # Detenemos la ejecución aquí, no hay nada más que imprimir
        
        # Evento 1: Suscripción exitosa
        elif evento == "pusher_internal:subscription_succeeded":
            print("[+] ¡Conectado al chat en vivo! Esperando mensajes...\n" + "="*50)
            
        # Evento 2: Alguien escribió en el chat
        elif evento == "App\\Events\\ChatMessageEvent":
            chat_data = json.loads(data.get("data", "{}"))
            usuario = chat_data.get("sender", {}).get("username", "Desconocido")
            contenido = chat_data.get("content", "")
            
            # Imprimir en consola
            print(f"[{usuario}]: {contenido}")
            
        # Evento 3: Error de Pusher (ej. la Key del .env caducó)
        elif evento == "pusher:error":
            error_msg = data.get("data", {}).get("message", "Error desconocido")
            print(f"[-] ERROR DE PUSHER: {error_msg}")
            print("[!] PISTA: Es probable que KICK_PUSHER_KEY haya cambiado. Revisa las herramientas de desarrollador en tu navegador.")
            
    except Exception as e:
        print(f"[!] Error procesando el paquete del socket: {e}")

def on_error(ws, error):
    print(f"[!] Error de conexión del WebSocket: {error}")

def on_close(ws, close_status_code, close_msg):
    print("\n[*] Conexión WebSocket cerrada.")

def on_open(ws, chatroom_id):
    """Se ejecuta apenas el WebSocket se abre; aquí solicitamos entrar al canal"""
    print(f"[*] Conexión física establecida. Suscribiéndose al canal de chat...")
    
    suscripcion = {
        "event": "pusher:subscribe",
        "data": {
            "auth": "",
            "channel": f"chatrooms.{chatroom_id}.v2"
        }
    }
    ws.send(json.dumps(suscripcion))

# ==========================================
# FLUJO PRINCIPAL
# ==========================================
if __name__ == "__main__":
    print("=== LECTOR DE CHAT KICK ===")
    
    streamer = input("Ingresa el nombre del streamer (ej. theandro2k): ").strip().lower()
    
    if not streamer:
        print("[-] Nombre inválido. Saliendo...")
        exit()

    # 1. Obtener el ID
    CHATROOM_ID = obtener_chatroom_id(streamer)
    
    if not CHATROOM_ID:
        exit()

    # 2. Configurar la URL de conexión a Pusher
    ws_url = f"wss://ws-{PUSHER_CLUSTER}.pusher.com/app/{PUSHER_KEY}?protocol=7&client=js&version=8.4.0-rc2&flash=false"
    
    # 3. Iniciar el WebSocket de forma continua
    wsapp = websocket.WebSocketApp(
        ws_url,
        on_open=lambda ws: on_open(ws, CHATROOM_ID),
        on_message=on_message,
        on_error=on_error,
        on_close=on_close
    )
    
    # Mantener el script corriendo eternamente con Pings automáticos cada 30 segundos
    wsapp.run_forever(ping_interval=30, ping_timeout=10)