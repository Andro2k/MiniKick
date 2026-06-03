# backend/kick_api_client.py

import cloudscraper
import requests
from backend.interfaces.auth_interfaces import TokenProvider

KICK_API_URL = "https://api.kick.com/public/v1/users"
KICK_CHANNEL_URL = "https://kick.com/api/v1/channels/{username}"
KICK_REWARDS_URL = "https://api.kick.com/public/v1/channels/rewards"
KICK_REDEMPTIONS_URL = "https://api.kick.com/public/v1/channels/rewards/redemptions"

class KickAPIClient:
    """Cliente HTTP para interactuar con la API REST de Kick."""
    
    def __init__(self, auth_provider: TokenProvider):
        self.auth_provider = auth_provider
        # Reutilizamos la misma instancia del scraper (Alta Cohesión/Rendimiento)
        self.scraper = cloudscraper.create_scraper()

    def _request(self, method: str, url: str, **kwargs) -> requests.Response:
        """
        [DRY PRINCIPLE]
        Centraliza la ejecución de peticiones HTTP con inyección automática 
        del Token y lógica de reintento si el token expira (401).
        """
        tokens = self.auth_provider.get_tokens()
        access_token = tokens.get("access_token", "")
        
        headers = kwargs.pop("headers", {})
        headers["Authorization"] = f"Bearer {access_token}"
        
        try:
            response = requests.request(method, url, headers=headers, **kwargs)
            response.raise_for_status()
            return response
        except requests.exceptions.HTTPError as e:
            if e.response is not None and e.response.status_code == 401:
                # Si el token expiró, refrescamos y reintentamos UNA sola vez (YAGNI)
                self.auth_provider.refresh_token()
                tokens = self.auth_provider.get_tokens()
                headers["Authorization"] = f"Bearer {tokens.get('access_token', '')}"
                
                retry_response = requests.request(method, url, headers=headers, **kwargs)
                retry_response.raise_for_status()
                return retry_response
            raise e

    def fetch_user_data(self) -> dict:
        # 1. Obtener datos del usuario autenticado
        resp = self._request("GET", KICK_API_URL, timeout=10)
        data = resp.json().get("data", [resp.json()])
        username = data[0].get("name")

        # 2. Obtener datos públicos del canal con el scraper
        url_slug = username.replace("_", "-").replace(" ", "")        
        channel_resp = self.scraper.get(KICK_CHANNEL_URL.format(username=url_slug))
        
        if channel_resp.status_code != 200:
            raise ValueError(f"No se pudo localizar el canal usando el slug: {url_slug}")
            
        channel_data = channel_resp.json()
        
        return {
            "username": username,
            "room_id": channel_data.get("chatroom", {}).get("id"),
            "followers": channel_data.get("followersCount", 0),
            "is_verified": channel_data.get("user", {}).get("is_verified", False),
            "playback_url": channel_data.get("playback_url", ""),
            "avatar_url": channel_data.get("user", {}).get("profile_pic", "")
        }

    def fetch_pending_redemptions(self, cursor: str = "") -> dict:
        url = f"{KICK_REDEMPTIONS_URL}?status=pending"
        if cursor:
            url += f"&cursor={cursor}"
            
        return self._request("GET", url, timeout=10).json()

    def fetch_channel_rewards(self) -> dict:
        return self._request("GET", KICK_REWARDS_URL, timeout=10).json()

    def accept_redemptions(self, redemption_ids: list[str]) -> dict:
        if not redemption_ids:
            return {}
            
        url = f"{KICK_REDEMPTIONS_URL}/accept"
        payload = {"ids": redemption_ids}
        
        # 'requests' inyecta automáticamente el Content-Type correcto al usar json=payload
        return self._request("POST", url, json=payload, timeout=10).json()