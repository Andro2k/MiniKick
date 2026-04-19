import os
import json
import sqlite3
import webbrowser
import urllib.parse
from http.server import BaseHTTPRequestHandler, HTTPServer
import requests
import base64
import hashlib
import secrets
import websocket
from curl_cffi import requests as cffi_requests
from dotenv import load_dotenv

# ==========================================
# 1. CONFIGURACIÓN INICIAL
# ==========================================
load_dotenv()
CLIENT_ID = os.getenv("KICK_CLIENT_ID")
CLIENT_SECRET = os.getenv("KICK_CLIENT_SECRET")
REDIRECT_URI = os.getenv("KICK_REDIRECT_URI")
PORT = int(os.getenv("PORT", 8080))
PUSHER_KEY = os.getenv("KICK_PUSHER_KEY")
PUSHER_CLUSTER = os.getenv("KICK_PUSHER_CLUSTER", "us2")

DB_FILE = "minikick.db"

# ==========================================
# 2. BASE DE DATOS LOCAL (SQLite)
# ==========================================
def iniciar_db():
    """Crea la tabla si no existe"""
    conexion = sqlite3.connect(DB_FILE)
    cursor = conexion.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS sesion (
            id INTEGER PRIMARY KEY,
            access_token TEXT,
            refresh_token TEXT,
            username TEXT,
            chatroom_id INTEGER
        )
    ''')
    conexion.commit()
    conexion.close()

def guardar_sesion(access_token, refresh_token, username, chatroom_id):
    """Guarda o actualiza la sesión del usuario"""
    conexion = sqlite3.connect(DB_FILE)
    cursor = conexion.cursor()
    # Borramos cualquier sesión anterior (solo queremos un usuario activo)
    cursor.execute('DELETE FROM sesion')
    cursor.execute('''
        INSERT INTO sesion (access_token, refresh_token, username, chatroom_id)
        VALUES (?, ?, ?, ?)
    ''', (access_token, refresh_token, username, chatroom_id))
    conexion.commit()
    conexion.close()

def cargar_sesion():
    """Devuelve los datos de sesión si existen, sino None"""
    conexion = sqlite3.connect(DB_FILE)
    cursor = conexion.cursor()
    cursor.execute('SELECT access_token, refresh_token, username, chatroom_id FROM sesion LIMIT 1')
    resultado = cursor.fetchone()
    conexion.close()
    
    if resultado:
        return {
            "access_token": resultado[0],
            "refresh_token": resultado[1],
            "username": resultado[2],
            "chatroom_id": resultado[3]
        }
    return None

def borrar_sesion():
    conexion = sqlite3.connect(DB_FILE)
    cursor = conexion.cursor()
    cursor.execute('DELETE FROM sesion')
    conexion.commit()
    conexion.close()

# ==========================================
# 3. AUTENTICACIÓN (OAuth 2.1 PKCE)
# ==========================================
codigo_autorizacion = None
estado_recibido = None

class OAuthHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        global codigo_autorizacion, estado_recibido
        parsed_path = urllib.parse.urlparse(self.path)
        if parsed_path.path == "/auth/callback":
            query_params = urllib.parse.parse_qs(parsed_path.query)
            if 'code' in query_params:
                codigo_autorizacion = query_params['code'][0]
                estado_recibido = query_params.get('state', [None])[0]
                self.send_response(200)
                self.send_header('Content-type', 'text/html; charset=utf-8')
                self.end_headers()
                self.wfile.write(b"<html><body style='background:#0b0e0f;color:#53fc18;text-align:center;padding:50px;font-family:sans-serif;'><h1>Login Exitoso</h1><p>Vuelve a la terminal.</p></body></html>")
            else:
                self.send_response(400)
                self.end_headers()
    def log_message(self, format, *args): pass

def autenticar_usuario():
    global codigo_autorizacion, estado_recibido
    codigo_autorizacion = None # Reiniciar por si acaso
    
    # PKCE
    code_verifier = secrets.token_urlsafe(64)
    hasher = hashlib.sha256(code_verifier.encode('ascii'))
    code_challenge = base64.urlsafe_b64encode(hasher.digest()).rstrip(b'=').decode('ascii')
    state_generado = secrets.token_urlsafe(16)

    params = {
        "client_id": CLIENT_ID, "redirect_uri": REDIRECT_URI, "response_type": "code",
        "scope": "user:read channel:read chat:write", "state": state_generado,
        "code_challenge": code_challenge, "code_challenge_method": "S256"
    }
    url_completa = f"https://id.kick.com/oauth/authorize?{urllib.parse.urlencode(params)}"

    servidor = HTTPServer(('localhost', PORT), OAuthHandler)
    print("\n[*] Abriendo el navegador para iniciar sesión en Kick...")
    webbrowser.open(url_completa)

    while codigo_autorizacion is None:
        servidor.handle_request()

    if estado_recibido != state_generado:
        print("[-] Error de seguridad PKCE.")
        return None

    print("[*] Obteniendo Access Token...")
    payload = {
        "grant_type": "authorization_code", "client_id": CLIENT_ID,
        "client_secret": CLIENT_SECRET, "redirect_uri": REDIRECT_URI,
        "code": codigo_autorizacion, "code_verifier": code_verifier
    }
    response = requests.post("https://id.kick.com/oauth/token", data=payload)
    
    if response.status_code == 200:
        return response.json()
    else:
        print(f"[-] Error OAuth: {response.text}")
        return None

# ==========================================
# 4. EXTRACCIÓN DE DATOS DEL CANAL
# ==========================================
def obtener_mi_perfil(access_token):
    """Llama a la API oficial SIN parámetros para saber quién está logueado"""
    url = "https://api.kick.com/public/v1/channels"
    headers = {"Authorization": f"Bearer {access_token}", "Accept": "application/json"}
    
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        data = response.json().get("data", [])
        if data:
            return data[0].get("slug") # Devuelve el username
    return None

def obtener_chatroom_id(streamer):
    """Scraping interno usando curl_cffi"""
    url = f"https://kick.com/api/v1/channels/{streamer}"
    try:
        response = cffi_requests.get(url, impersonate="chrome124", timeout=10)
        if response.status_code == 200:
            return response.json().get("chatroom", {}).get("id")
    except:
        pass
    return None

# ==========================================
# 5. LECTOR DE CHAT (WebSockets)
# ==========================================
def on_message(ws, message):
    data = json.loads(message)
    evento = data.get("event")
    
    if evento == "pusher:ping":
        ws.send(json.dumps({"event": "pusher:pong", "data": {}}))
    elif evento == "pusher_internal:subscription_succeeded":
        print("[+] ¡Conectado al chat! Esperando mensajes...\n" + "="*50)
    elif evento == "App\\Events\\ChatMessageEvent":
        chat_data = json.loads(data.get("data", "{}"))
        usuario = chat_data.get("sender", {}).get("username", "Desconocido")
        print(f"[{usuario}]: {chat_data.get('content', '')}")

def iniciar_chat(chatroom_id):
    ws_url = f"wss://ws-{PUSHER_CLUSTER}.pusher.com/app/{PUSHER_KEY}?protocol=7&client=js&version=8.4.0-rc2&flash=false"
    
    wsapp = websocket.WebSocketApp(
        ws_url,
        on_open=lambda ws: ws.send(json.dumps({"event": "pusher:subscribe", "data": {"auth": "", "channel": f"chatrooms.{chatroom_id}.v2"}})),
        on_message=on_message,
        on_error=lambda ws, e: print(f"[!] Error: {e}"),
        on_close=lambda ws, a, b: print("\n[*] Desconectado del chat.")
    )
    wsapp.run_forever(ping_interval=30, ping_timeout=10)

# ==========================================
# FLUJO PRINCIPAL AUTOMATIZADO
# ==========================================
if __name__ == "__main__":
    print("=== MiniKick: Inicio Automático ===")
    iniciar_db()
    sesion = cargar_sesion()

    if not sesion:
        print("[!] No hay sesión guardada en la base de datos.")
        tokens = autenticar_usuario()
        
        if tokens:
            access_token = tokens.get("access_token")
            refresh_token = tokens.get("refresh_token")
            
            print("[*] Identificando tu canal en Kick...")
            mi_usuario = obtener_mi_perfil(access_token)
            
            if mi_usuario:
                print(f"[+] Hola, {mi_usuario}! Buscando tu Chatroom ID...")
                mi_chatroom = obtener_chatroom_id(mi_usuario)
                
                if mi_chatroom:
                    print(f"[+] Guardando datos en base de datos local (minikick.db)...")
                    guardar_sesion(access_token, refresh_token, mi_usuario, mi_chatroom)
                    sesion = cargar_sesion() # Recargamos para usarla abajo
                else:
                    print("[-] No se pudo obtener el Chatroom ID.")
            else:
                print("[-] No se pudo leer tu perfil de Kick.")
        else:
            print("[-] Falló la autenticación. Saliendo.")
            exit()
    
    if sesion:
        print(f"\n[+] BIENVENIDO DE VUELTA: {sesion['username']}")
        print(f"[*] Conectando automáticamente al Chatroom: {sesion['chatroom_id']}")
        iniciar_chat(sesion['chatroom_id'])