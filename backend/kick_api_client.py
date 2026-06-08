# backend/kick_api_client.py

import time

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
        self.scraper = cloudscraper.create_scraper()

    def _request(self, method: str, url: str, **kwargs) -> requests.Response:
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
                self.auth_provider.refresh_token()
                tokens = self.auth_provider.get_tokens()
                headers["Authorization"] = f"Bearer {tokens.get('access_token', '')}"
                
                retry_response = requests.request(method, url, headers=headers, **kwargs)
                retry_response.raise_for_status()
                return retry_response
            raise e

    def fetch_user_data(self) -> dict:
        """Orquesta la obtención y mapeo de los datos del canal del usuario."""
        username = self._fetch_authenticated_username()
        channel_data = self._fetch_channel_details(username)
        return self._map_channel_data(username, channel_data)

    def _fetch_authenticated_username(self) -> str:
        """Responsabilidad única: Obtener el nombre de usuario autenticado."""
        resp = self._request("GET", KICK_API_URL, timeout=10)
        data = resp.json().get("data", [resp.json()])
        return data[0].get("name")

    def _fetch_channel_details(self, username: str, max_retries: int = 3) -> dict:
        """
        Responsabilidad única: Obtener la data en crudo del canal mediante scraper, 
        manejando automáticamente los bloqueos transitorios de Cloudflare (muy comunes en Linux).
        """
        url = KICK_CHANNEL_URL.format(username=username)
        
        for attempt in range(max_retries):
            channel_resp = self.scraper.get(url)
            
            if channel_resp.status_code == 200:
                return channel_resp.json()
            if attempt < max_retries - 1:
                time.sleep(2 * (attempt + 1))
                
        # Si agotamos todos los intentos, entonces sí lanzamos el error hacia la UI
        raise ValueError(f"No se pudo localizar el canal usando el usuario: {username} tras {max_retries} intentos.")

    def _map_channel_data(self, username: str, channel_data: dict) -> dict:
        """Responsabilidad única: Formatear la respuesta externa a nuestro formato interno."""
        user_data = channel_data.get("user", {})
        chatroom_data = channel_data.get("chatroom", {})
        followers = channel_data.get("followers_count", channel_data.get("followersCount", 0))
        
        return {
            "username": username,
            "room_id": chatroom_data.get("id"),
            "followers": followers,
            "is_verified": user_data.get("is_verified", False),
            "playback_url": channel_data.get("playback_url", ""),
            "avatar_url": user_data.get("profile_pic", "")
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
        return self._request("POST", url, json=payload, timeout=10).json()