import os
import json
import webbrowser
import urllib.parse
from http.server import BaseHTTPRequestHandler, HTTPServer
import requests
import base64
import hashlib
import secrets
from dotenv import load_dotenv

# 1. Cargar las credenciales del .env
load_dotenv()

CLIENT_ID = os.getenv("KICK_CLIENT_ID")
CLIENT_SECRET = os.getenv("KICK_CLIENT_SECRET")
REDIRECT_URI = os.getenv("KICK_REDIRECT_URI")
PORT = int(os.getenv("PORT", 8080))
TOKEN_FILE = "kick_token.json"

# Endpoints oficiales según la documentación de Kick
AUTH_URL = "https://id.kick.com/oauth/authorize"
TOKEN_URL = "https://id.kick.com/oauth/token"

# Variables globales para el flujo
codigo_autorizacion = None
estado_recibido = None

# ==========================================
# GENERACIÓN DE PKCE Y STATE
# ==========================================
# 1. Generar un Verificador (Code Verifier) aleatorio
code_verifier = secrets.token_urlsafe(64)

# 2. Hashear el Verificador con SHA256 y codificarlo en Base64URL para crear el Reto (Code Challenge)
hasher = hashlib.sha256(code_verifier.encode('ascii'))
code_challenge = base64.urlsafe_b64encode(hasher.digest()).rstrip(b'=').decode('ascii')

# 3. Generar un "State" aleatorio por seguridad
state_generado = secrets.token_urlsafe(16)


class OAuthCallbackHandler(BaseHTTPRequestHandler):
    """Mini-servidor para atrapar la redirección de Kick"""
    def do_GET(self):
        global codigo_autorizacion
        global estado_recibido
        
        parsed_path = urllib.parse.urlparse(self.path)
        
        if parsed_path.path == "/auth/callback":
            query_params = urllib.parse.parse_qs(parsed_path.query)
            
            if 'code' in query_params:
                codigo_autorizacion = query_params['code'][0]
                estado_recibido = query_params.get('state', [None])[0]
                
                self.send_response(200)
                self.send_header('Content-type', 'text/html; charset=utf-8')
                self.end_headers()
                html = """
                <html><body style="background-color:#0b0e0f; color:#53fc18; font-family:sans-serif; text-align:center; padding-top:50px;">
                    <h1>¡Autenticación Kick Exitosa!</h1>
                    <p>MiniKick ha recibido el código. Ya puedes cerrar esta pestaña y volver a la terminal.</p>
                </body></html>
                """
                self.wfile.write(html.encode('utf-8'))
            else:
                self.send_response(400)
                self.end_headers()
                self.wfile.write(b"Error: No se recibio el codigo.")
                
    def log_message(self, format, *args):
        pass # Silenciar logs

def obtener_token_kick():
    global codigo_autorizacion
    
    if not CLIENT_ID or not CLIENT_SECRET:
        print("[-] ERROR: Faltan KICK_CLIENT_ID o KICK_CLIENT_SECRET en tu archivo .env")
        return

    # 1. Preparar la URL de autorización con PKCE y State
    params = {
        "client_id": CLIENT_ID,
        "redirect_uri": REDIRECT_URI,
        "response_type": "code",
        "scope": "user:read channel:read chat:write",
        "state": state_generado,
        "code_challenge": code_challenge,
        "code_challenge_method": "S256"
    }
    url_completa = f"{AUTH_URL}?{urllib.parse.urlencode(params)}"

    print(f"[*] Levantando servidor local en el puerto {PORT}...")
    servidor = HTTPServer(('localhost', PORT), OAuthCallbackHandler)

    print("[*] Abriendo el navegador para autorizar la aplicación en Kick...")
    webbrowser.open(url_completa)

    print("[*] Esperando a que el usuario inicie sesión y acepte...")
    while codigo_autorizacion is None:
        servidor.handle_request()

    # Verificación de seguridad del estado
    if estado_recibido != state_generado:
        print("[-] ERROR DE SEGURIDAD: El parámetro 'state' recibido no coincide. Posible ataque CSRF.")
        return

    print(f"[+] ¡Código recibido con éxito!")
    print("[*] Intercambiando el código por un Access Token...")

    # 2. Hacer la petición POST para obtener el Token
    payload = {
        "grant_type": "authorization_code",
        "client_id": CLIENT_ID,
        "client_secret": CLIENT_SECRET,
        "redirect_uri": REDIRECT_URI,
        "code": codigo_autorizacion,
        "code_verifier": code_verifier  # Kick verifica que coincida con el code_challenge enviado antes
    }
    
    headers = {
        "Content-Type": "application/x-www-form-urlencoded",
        "Accept": "application/json"
    }

    try:
        response = requests.post(TOKEN_URL, data=payload, headers=headers)
        
        if response.status_code == 200:
            token_data = response.json()
            
            with open(TOKEN_FILE, "w") as f:
                json.dump(token_data, f, indent=4)
                
            print(f"[+] ¡Éxito! Token guardado correctamente en {TOKEN_FILE}")
            
            # Mostrar datos útiles
            print(f"    - Access Token: {token_data.get('access_token')[:15]}...")
            print(f"    - Expira en: {token_data.get('expires_in')} segundos")
        else:
            print(f"[-] Error al obtener el token (HTTP {response.status_code})")
            print("Detalles:", response.text)
            
    except Exception as e:
        print(f"[-] Error de conexión durante el intercambio: {e}")

if __name__ == "__main__":
    print("=== MiniKick OAuth 2.1 PKCE Manager ===")
    
    if os.path.exists(TOKEN_FILE):
        print(f"[*] Se encontró el archivo {TOKEN_FILE}.")
        opcion = input("¿Deseas generar uno nuevo de todos modos? (s/n): ").lower()
        if opcion == 's':
            obtener_token_kick()
        else:
            print("[*] Proceso cancelado.")
    else:
        obtener_token_kick()