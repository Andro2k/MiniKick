import webbrowser
import urllib.parse
from http.server import BaseHTTPRequestHandler, HTTPServer
import requests
import base64
import hashlib
import secrets
from backend.connection.config import CLIENT_ID, CLIENT_SECRET, REDIRECT_URI, PORT

# Variables globales para el servidor temporal
codigo_autorizacion = None
estado_recibido = None

class OAuthHandler(BaseHTTPRequestHandler):
    """Mini-servidor web para atrapar la redirección de Kick"""
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
        pass # Silenciar los logs en la consola

def autenticar_usuario():
    """Ejecuta el flujo OAuth 2.1 PKCE y devuelve los tokens (o None si falla)"""
    global codigo_autorizacion, estado_recibido
    codigo_autorizacion = None 
    
    if not CLIENT_ID or not CLIENT_SECRET:
        print("[-] Error: Faltan credenciales en el archivo .env")
        return None

    # Generar seguridad PKCE
    code_verifier = secrets.token_urlsafe(64)
    hasher = hashlib.sha256(code_verifier.encode('ascii'))
    code_challenge = base64.urlsafe_b64encode(hasher.digest()).rstrip(b'=').decode('ascii')
    state_generado = secrets.token_urlsafe(16)

    params = {
        "client_id": CLIENT_ID,
        "redirect_uri": REDIRECT_URI,
        "response_type": "code",
        "scope": "user:read channel:read chat:write",
        "state": state_generado,
        "code_challenge": code_challenge,
        "code_challenge_method": "S256"
    }
    
    url_completa = f"https://id.kick.com/oauth/authorize?{urllib.parse.urlencode(params)}"

    print("\n[*] Abriendo el navegador para iniciar sesión en Kick...")
    servidor = HTTPServer(('localhost', PORT), OAuthHandler)
    webbrowser.open(url_completa)

    # Esperar hasta que el navegador nos devuelva el código
    while codigo_autorizacion is None:
        servidor.handle_request()

    if estado_recibido != state_generado:
        print("[-] Error crítico: Posible ataque CSRF. El 'state' no coincide.")
        return None

    print("[*] Obteniendo Access Token oficial...")
    payload = {
        "grant_type": "authorization_code",
        "client_id": CLIENT_ID,
        "client_secret": CLIENT_SECRET,
        "redirect_uri": REDIRECT_URI,
        "code": codigo_autorizacion,
        "code_verifier": code_verifier
    }
    
    try:
        response = requests.post("https://id.kick.com/oauth/token", data=payload)
        if response.status_code == 200:
            return response.json()
        else:
            print(f"[-] Error OAuth HTTP {response.status_code}: {response.text}")
    except Exception as e:
        print(f"[-] Error de red durante la autenticación: {e}")
        
    return None