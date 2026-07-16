# backend\providers\music\spotify_client.py

import base64
import requests
from urllib.parse import urlparse, urlencode, quote
from backend.services.auth.oauth_service import OAuthCallbackServer

SPOTIFY_AUTH_URL = "https://accounts.spotify.com/authorize"
SPOTIFY_TOKEN_URL = "https://accounts.spotify.com/api/token"
SPOTIFY_API_BASE = "https://api.spotify.com/v1"

class SpotifyAuthManager:
    def __init__(self, client_id: str, client_secret: str, redirect_uri: str, storage, success_html_path: str = ""):
        self.client_id = client_id
        self.client_secret = client_secret
        self.redirect_uri = redirect_uri
        self.storage = storage
        self.success_html_path = success_html_path

    def get_access_token(self) -> str | None:
        tokens = self.storage.load()
        return tokens.get("access_token") if tokens else None

    def login(self) -> dict:
        scopes = "user-read-currently-playing user-modify-playback-state"
        params = {
            "client_id": self.client_id,
            "response_type": "code",
            "redirect_uri": self.redirect_uri,
            "scope": scopes,
            "show_dialog": "true"
        }
        auth_url = f"{SPOTIFY_AUTH_URL}?{urlencode(params)}"
        
        port = int(urlparse(self.redirect_uri).port or 8080)
        auth_code = OAuthCallbackServer.capture_auth_code(auth_url, port, self.success_html_path, provider="spotify")
        if not auth_code:
            raise TimeoutError("Auth timeout")
        return self._exchange_code(auth_code)

    def refresh_token(self) -> dict | None:
        tokens = self.storage.load()
        refresh_token = tokens.get("refresh_token") if tokens else None
        if not refresh_token:
            return None

        auth_header = base64.b64encode(f"{self.client_id}:{self.client_secret}".encode()).decode()
        try:
            resp = requests.post(
                SPOTIFY_TOKEN_URL,
                headers={"Authorization": f"Basic {auth_header}"},
                data={"grant_type": "refresh_token", "refresh_token": refresh_token}
            )
            resp.raise_for_status()
            new_tokens = resp.json()
            if "refresh_token" not in new_tokens:
                new_tokens["refresh_token"] = refresh_token
            self.storage.save(new_tokens)
            return new_tokens
        except requests.exceptions.RequestException:
            return None

    def _exchange_code(self, code: str) -> dict:
        auth_header = base64.b64encode(f"{self.client_id}:{self.client_secret}".encode()).decode()
        resp = requests.post(
            SPOTIFY_TOKEN_URL,
            headers={"Authorization": f"Basic {auth_header}"},
            data={
                "grant_type": "authorization_code",
                "code": code,
                "redirect_uri": self.redirect_uri
            }
        )
        resp.raise_for_status()
        tokens = resp.json()
        self.storage.save(tokens)
        return tokens

    def logout(self):
        self.storage.clear()

class SpotifyMusicProvider:    
    def __init__(self, auth_manager: SpotifyAuthManager, i18n, db_manager=None):
        self.auth = auth_manager
        self.i18n = i18n
        self.db_manager = db_manager

    @property
    def provider_id(self) -> str:
        return "spotify"

    def _request(self, method: str, endpoint: str, **kwargs) -> requests.Response:
        token = self.auth.get_access_token()
        if not token:
            raise PermissionError(self.i18n.get("music.errors.no_session"))
        headers = kwargs.pop("headers", {})
        headers["Authorization"] = f"Bearer {token}"
        url = f"{SPOTIFY_API_BASE}{endpoint}"
        resp = requests.request(method, url, headers=headers, **kwargs)
        if resp.status_code == 401:
            new_tokens = self.auth.refresh_token()
            if not new_tokens:
                raise PermissionError(self.i18n.get("music.errors.refresh_failed"))
            headers["Authorization"] = f"Bearer {new_tokens['access_token']}"
            resp = requests.request(method, url, headers=headers, **kwargs)
        return resp

    def get_current_song(self) -> dict | None:
        try:
            resp = self._request("GET", "/me/player/currently-playing")
            if resp.status_code == 204:
                return None
            data = resp.json()
            item = data.get("item")
            if not item:
                return None
            artists = ", ".join(a.get("name") for a in item.get("artists", []))
            return {
                "title": item.get("name", self.i18n.get("music.player.unknown_song")),
                "artist": artists,
                "url": item.get("external_urls", {}).get("spotify", ""),
                "is_playing": data.get("is_playing", False)
            }
        except Exception:
            return None

    def add_to_queue(self, query_or_uri: str, callback=None, requester: str = None) -> tuple[bool, str]:
        try:
            track_uri = query_or_uri.strip()
            track_name = track_uri
            if not track_uri.startswith("spotify:track:"):
                search_resp = self._request("GET", f"/search?q={quote(track_uri)}&type=track&limit=1")
                tracks = search_resp.json().get("tracks", {}).get("items", [])
                if not tracks:
                    msg = self.i18n.get("music.queue.not_found").replace("{query}", query_or_uri)
                    return False, msg         
                target = tracks[0]
                track_uri = target.get("uri")
                artists = ", ".join(a.get("name") for a in target.get("artists", []))
                track_name = f"{target.get('name')} - {artists}"

            resp = self._request("POST", f"/me/player/queue?uri={track_uri}")
            resp.raise_for_status()
            
            title = track_name
            artist = ""
            if " - " in track_name:
                title, artist = track_name.split(" - ", 1)
            
            if self.db_manager:
                self.db_manager.add_song_to_queue(
                    title=title,
                    artist=artist,
                    url=track_uri,
                    requester=requester,
                    provider="spotify"
                )
            
            msg = self.i18n.get("music.queue.success").replace("{track}", track_name)
            return True, msg

        except requests.exceptions.HTTPError as e:
            if "NO_ACTIVE_DEVICE" in e.response.text:
                msg = self.i18n.get("music.queue.no_device")
            else:
                msg = self.i18n.get("music.queue.rejected").replace("{status}", str(e.response.status_code))
            return False, msg
        except Exception as e:
            msg = self.i18n.get("music.queue.error").replace("{error}", str(e))
            return False, msg

    def skip_current(self) -> bool:
        try:
            resp = self._request("POST", "/me/player/next")
            return 200 <= resp.status_code < 300
        except Exception:
            return False

    def set_volume(self, volume: int) -> None:
        pass

    def pause_playback(self) -> bool:
        try:
            resp = self._request("PUT", "/me/player/pause")
            return 200 <= resp.status_code < 300
        except Exception:
            return False

    def resume_playback(self) -> bool:
        try:
            resp = self._request("PUT", "/me/player/play")
            return 200 <= resp.status_code < 300
        except Exception:
            return False
