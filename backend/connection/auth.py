import webbrowser
import urllib.parse
from http.server import BaseHTTPRequestHandler, HTTPServer
import requests
import base64
import hashlib
import secrets
from backend.connection.config import Config

def autenticar_usuario():
    """Ejecuta el flujo OAuth 2.1 PKCE y devuelve los tokens (o None si falla)."""
    
    # Validamos antes de intentar hacer nada
    Config.validar_credenciales()

    # Diccionario para guardar el estado sin usar variables globales
    auth_state = {'code': None, 'received_state': None}

    # Generar seguridad PKCE
    code_verifier = secrets.token_urlsafe(64)
    hasher = hashlib.sha256(code_verifier.encode('ascii'))
    code_challenge = base64.urlsafe_b64encode(hasher.digest()).rstrip(b'=').decode('ascii')
    state_generado = secrets.token_urlsafe(16)

    class OAuthHandler(BaseHTTPRequestHandler):
        """Mini-servidor web encapsulado para atrapar la redirección."""
        def do_GET(self):
            parsed_path = urllib.parse.urlparse(self.path)
            
            if parsed_path.path == "/auth/callback":
                query_params = urllib.parse.parse_qs(parsed_path.query)
                if 'code' in query_params:
                    auth_state['code'] = query_params['code'][0]
                    auth_state['received_state'] = query_params.get('state', [None])[0]
                    
                    self.send_response(200)
                    self.send_header('Content-type', 'text/html; charset=utf-8')
                    self.end_headers()
                    html = """
                    <html><body style='background:#0b0e0f;color:#53fc18;text-align:center;padding:50px;font-family:sans-serif;'>
                        <h1>¡Login Exitoso!</h1>
                        <p>MiniKick ha sido autorizado. Ya puedes cerrar esta ventana y volver a la terminal.</p>
                    </body></html>
                    """
                    self.wfile.write(html.encode('utf-8'))
                else:
                    self.send_response(400)
                    self.end_headers()
                    
        def log_message(self, format, *args):
            pass # Silenciar logs

    params = {
        "client_id": Config.CLIENT_ID,
        "redirect_uri": Config.REDIRECT_URI,
        "response_type": "code",
        "scope": "user:read channel:read chat:write channel:rewards:read channel:rewards:write",
        "state": state_generado,
        "code_challenge": code_challenge,
        "code_challenge_method": "S256"
    }
    
    url_completa = f"https://id.kick.com/oauth/authorize?{urllib.parse.urlencode(params)}"

    print("\n[*] Abriendo el navegador para iniciar sesión en Kick...")
    servidor = HTTPServer(('localhost', Config.PORT), OAuthHandler)
    webbrowser.open(url_completa)

    # Esperar el código manejando las peticiones
    while auth_state['code'] is None:
        servidor.handle_request()
        
    # Cerrar el servidor explícitamente para liberar el puerto
    servidor.server_close()

    if auth_state['received_state'] != state_generado:
        print("[-] Error crítico: Posible ataque CSRF. El 'state' no coincide.")
        return None

    print("[*] Obteniendo Access Token oficial...")
    payload = {
        "grant_type": "authorization_code",
        "client_id": Config.CLIENT_ID,
        "client_secret": Config.CLIENT_SECRET,
        "redirect_uri": Config.REDIRECT_URI,
        "code": auth_state['code'],
        "code_verifier": code_verifier
    }
    
    try:
        response = requests.post("https://id.kick.com/oauth/token", data=payload, timeout=10)
        response.raise_for_status() # Lanza excepción si no es un 2XX
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"[-] Error de red durante la obtención del token: {e}")
        if response is not None:
            print(f"[-] Detalle: {response.text}")
        
    return None

def renovar_token(refresh_token):
    """Utiliza el refresh_token para obtener un nuevo access_token de Kick."""
    payload = {
        "grant_type": "refresh_token",
        "client_id": Config.CLIENT_ID,
        "client_secret": Config.CLIENT_SECRET,
        "refresh_token": refresh_token
    }
    
    try:
        response = requests.post("https://id.kick.com/oauth/token", data=payload, timeout=10)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"[-] Error al renovar token: {e}")
        
    return None