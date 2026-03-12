# backend/core/auth.py
import os
import base64
import hashlib
import urllib.parse
import webbrowser
import asyncio
from aiohttp import web
from backend.core.db_manager import DBManager

class KickAuthManager:
    """Gestiona los tokens OAuth, su almacenamiento y el flujo de autorización."""
    
    def __init__(self, client_id: str, client_secret: str, redirect_uri: str, db_manager: DBManager):
        self.client_id = client_id
        self.client_secret = client_secret
        self.redirect_uri = redirect_uri
        self.db = db_manager  # Guardamos la instancia de la DB
        self.access_token = None
        self.refresh_token = None
        self._load_tokens()

    def _load_tokens(self):
        """Lee los tokens desde SQLite en lugar de un JSON."""
        self.access_token = self.db.get_config("access_token")
        self.refresh_token = self.db.get_config("refresh_token")

    def save_tokens(self, data: dict):
        """Guarda los tokens en SQLite en lugar de un JSON."""
        self.access_token = data.get("access_token")
        self.refresh_token = data.get("refresh_token")
        
        if self.access_token:
            self.db.set_config("access_token", self.access_token)
        if self.refresh_token:
            self.db.set_config("refresh_token", self.refresh_token)

    def get_auth_headers(self) -> dict:
        if not self.access_token:
            return {}
        return {
            "Authorization": f"Bearer {self.access_token}",
            "Accept": "application/json"
        }

    async def execute_oauth_flow(self, session, log_callback) -> bool:
        """Abre el navegador y levanta un servidor local para obtener el código OAuth."""
        log_callback("⚠️ Token faltante o expirado. Abriendo navegador para Login OAuth...")
        
        # Generar códigos de seguridad PKCE
        verifier = base64.urlsafe_b64encode(os.urandom(32)).rstrip(b'=').decode('utf-8')
        challenge = base64.urlsafe_b64encode(hashlib.sha256(verifier.encode('utf-8')).digest()).rstrip(b'=').decode('utf-8')
        
        params = {
            "client_id": self.client_id, "code_challenge": challenge, "code_challenge_method": "S256",
            "redirect_uri": self.redirect_uri, "response_type": "code", "state": "kick_auth",
            "scope": "user:read channel:read channel:write chat:write events:subscribe channel:rewards:read channel:rewards:write"
        }
        auth_url = f"https://id.kick.com/oauth/authorize?{urllib.parse.urlencode(params)}"
        
        # Levantar mini-servidor web local para atrapar el redirect
        parsed_uri = urllib.parse.urlparse(self.redirect_uri)
        future_code = asyncio.Future()

        async def callback_handler(request):
            if code := request.query.get("code"):
                future_code.set_result(code)
                return web.Response(text="<h2>¡Exito!</h2><p>Ya puedes volver a MiniKick.</p>", content_type="text/html")
            return web.Response(text="Error de Login.", content_type="text/html")
            
        app = web.Application()
        app.router.add_get(parsed_uri.path, callback_handler)
        runner = web.AppRunner(app)
        await runner.setup()
        site = web.TCPSite(runner, parsed_uri.hostname, parsed_uri.port)
        await site.start()
        
        webbrowser.open(auth_url) 
        
        try:
            # Esperamos a que el usuario inicie sesión (máximo 2 minutos)
            code = await asyncio.wait_for(future_code, timeout=120) 
            log_callback("✅ Autorización concedida. Obteniendo tokens...")
            
            payload = {
                "grant_type": "authorization_code", "client_id": self.client_id, "client_secret": self.client_secret,
                "code": code, "redirect_uri": self.redirect_uri, "code_verifier": verifier
            }
            async with session.post("https://id.kick.com/oauth/token", data=payload) as resp:
                if resp.status == 200:
                    self.save_tokens(await resp.json())
                    return True
        except asyncio.TimeoutError:
            log_callback("❌ El tiempo de inicio de sesión expiró.")
        except Exception as e:
             log_callback(f"❌ Error inesperado en el flujo OAuth: {e}")
        finally:
            await site.stop()
            await runner.cleanup()
            
        return False