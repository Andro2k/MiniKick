# backend/core/api_client.py
import aiohttp
import cloudscraper
from typing import Tuple, Any
from backend.core.db_manager import DBManager
from backend.core.auth import KickAuthManager

class KickAPIClient:
    """Cliente HTTP asíncrono para interactuar con la API de Kick."""
    
    def __init__(self, client_id: str, client_secret: str, redirect_uri: str, db_manager: DBManager):
        self.auth = KickAuthManager(client_id, client_secret, redirect_uri, db_manager)
        self.session = None

    async def init_session(self):
        if not self.session:
            self.session = aiohttp.ClientSession()

    async def close(self):
        if self.session: 
            await self.session.close()

    async def refresh_token(self) -> bool:
        if not self.auth.refresh_token: 
            return False
            
        url = "https://id.kick.com/oauth/token"
        payload = {
            "grant_type": "refresh_token",
            "client_id": self.auth.client_id,
            "client_secret": self.auth.client_secret,
            "refresh_token": self.auth.refresh_token
        }
        async with self.session.post(url, data=payload) as resp:
            if resp.status == 200:
                new_data = await resp.json()
                if "refresh_token" not in new_data:
                    new_data["refresh_token"] = self.auth.refresh_token
                self.auth.save_tokens(new_data)
                return True
            return False

    async def request(self, method: str, url: str, **kwargs) -> Tuple[int, Any]:
        """Realiza una petición HTTP inyectando automáticamente los tokens de autorización."""
        if not self.session: 
            await self.init_session()
            
        headers = kwargs.pop("headers", {})
        headers.update(self.auth.get_auth_headers())

        async with self.session.request(method, url, headers=headers, **kwargs) as resp:
            if resp.status == 401:  
                # Si el token expiró, intentamos renovarlo y repetimos la petición
                if await self.refresh_token():
                    headers.update(self.auth.get_auth_headers())
                    async with self.session.request(method, url, headers=headers, **kwargs) as retry_resp:
                        return retry_resp.status, await retry_resp.json()
                else:
                    return 401, {"error": "Fallo al renovar token"}
            try:
                return resp.status, await resp.json()
            except:
                return resp.status, {}

    async def authenticate_if_needed(self, log_callback) -> bool:
        """Verifica si el token es válido o dispara el flujo OAuth."""
        await self.init_session()
        
        if self.auth.access_token:
            status, _ = await self.request("GET", "https://api.kick.com/public/v1/users")
            if status == 200: 
                return True 

        return await self.auth.execute_oauth_flow(self.session, log_callback)

    def fetch_channel_data_sync(self, slug: str) -> dict:
        """Hace scraping sincrónico para evadir Cloudflare y obtener datos públicos del canal."""
        scraper = cloudscraper.create_scraper()
        headers = self.auth.get_auth_headers()
        resp = scraper.get(f"https://kick.com/api/v1/channels/{slug}", headers=headers, timeout=10)
        
        if resp.status_code == 200:
            return resp.json()
        else:
            raise Exception(f"HTTP {resp.status_code}")
        
    async def update_reward(self, reward_id: str, payload: dict) -> Tuple[int, Any]:
        """Envía una petición a Kick para actualizar los datos de una recompensa."""
        url = f"https://api.kick.com/public/v1/channels/rewards/{reward_id}"
        # Usamos PUT (o PATCH) que es el estándar para actualizar en APIs REST
        return await self.request("PUT", url, json=payload)