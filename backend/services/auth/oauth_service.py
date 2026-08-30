# backend\services\auth\oauth_service.py

import base64
import hashlib
import logging
import os
import time
import webbrowser
from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import parse_qs, urlparse
import requests
from backend.interfaces import TokenStorage

logger = logging.getLogger("minikick.services.auth")

KICK_AUTH_URL = "https://id.kick.com/oauth/authorize"
KICK_TOKEN_URL = "https://id.kick.com/oauth/token"
TWITCH_AUTH_URL = "https://id.twitch.tv/oauth2/authorize"
TWITCH_TOKEN_URL = "https://id.twitch.tv/oauth2/token"

class _OAuthCallbackHandler(BaseHTTPRequestHandler):
    def do_GET(self) -> None:
        query = parse_qs(urlparse(self.path).query)
        code = query.get("code", [None])[0]
        error = query.get("error", [None])[0]
        
        if code or error:
            if code:
                self.server.auth_code = code
            else:
                self.server.auth_code = ""
                
            self.send_response(200)
            self.send_header("Content-type", "text/html; charset=utf-8")
            self.end_headers()
            
            html_path = getattr(self.server, "success_html_path", "")
            provider = getattr(self.server, "provider", "kick")
            status = "success" if code else "error"
            error_msg = query.get("error_description", [error])[0] if error else ""
            
            content = None
            if html_path and os.path.exists(html_path):
                try:
                    with open(html_path, "r", encoding="utf-8") as f:
                        template = f.read()
                    content = template.replace("{{PROVIDER}}", provider)
                    content = content.replace("{{STATUS}}", status)
                    content = content.replace("{{ERROR_MSG}}", error_msg)
                except Exception as e:
                    logger.warning("[OAuthCallback] Error reading auth template '%s': %s", html_path, e)

            if not content:
                status_text = "exitosa" if code else "fallida"
                status_en = "successful" if code else "failed"
                content = f"<h1>Autenticación {status_text} / Authentication {status_en}.</h1>"
                if error_msg:
                    content += f"<p>Error: {error_msg}</p>"

            try:
                self.wfile.write(content.encode("utf-8"))
            except (BrokenPipeError, ConnectionResetError):
                pass

    def log_message(self, *args) -> None:
        pass

class OAuthCallbackServer:
    @staticmethod
    def capture_auth_code(url: str, port: int, success_html_path: str, timeout_seconds: int = 120, provider: str = "kick") -> str | None:
        httpd = HTTPServer(("", port), _OAuthCallbackHandler)
        httpd.timeout = 1 
        httpd.auth_code = None
        httpd.success_html_path = success_html_path
        httpd.provider = provider
        
        webbrowser.open(url)
        start_time = time.time()
        
        while httpd.auth_code is None:
            if time.time() - start_time > timeout_seconds:
                break
            httpd.handle_request()
            
        httpd.server_close()
        return httpd.auth_code

class AuthManager:
    def __init__(self, client_id: str, client_secret: str, redirect_uri: str, storage: TokenStorage, success_html_path: str = "") -> None:
        self.client_id = client_id
        self.client_secret = client_secret
        self.redirect_uri = redirect_uri
        self.storage = storage
        self.success_html_path = success_html_path

    def get_tokens(self, force: bool = False) -> dict:
        if force:
            return self._new_login()
        tokens = self.storage.load()
        if tokens and "access_token" in tokens:
            return tokens
        return self._new_login()

    def refresh_token(self) -> dict:
        tokens = self.storage.load()
        refresh_token = tokens.get("refresh_token") if tokens else None

        if not refresh_token:
            return self._new_login()

        try:
            response = requests.post(
                KICK_TOKEN_URL,
                data={
                    "grant_type": "refresh_token",
                    "client_id": self.client_id,
                    "client_secret": self.client_secret,
                    "refresh_token": refresh_token,
                },
            )
            response.raise_for_status()
            new_tokens = response.json()
            self.storage.save(new_tokens)
            return new_tokens
        except requests.exceptions.RequestException:
            return self._new_login()

    def _new_login(self) -> dict:
        verifier, challenge = self._pkce_pair()
        auth_url = self._build_auth_url(challenge)

        port = int(urlparse(self.redirect_uri).port or 8080)
        auth_code = OAuthCallbackServer.capture_auth_code(auth_url, port, self.success_html_path, provider="kick")

        if not auth_code:
            raise TimeoutError("Auth timeout or user canceled login.")

        tokens = self._exchange_code(auth_code, verifier)
        self.storage.save(tokens)
        return tokens

    @staticmethod
    def _pkce_pair() -> tuple[str, str]:
        verifier = base64.urlsafe_b64encode(os.urandom(32)).decode().rstrip("=")
        challenge = base64.urlsafe_b64encode(hashlib.sha256(verifier.encode()).digest()).decode().rstrip("=")
        return verifier, challenge

    def _build_auth_url(self, challenge: str) -> str:
        scopes = "user:read channel:read channel:write channel:rewards:read channel:rewards:write chat:write moderation:ban moderation:chat_message:manage"
        return (
            f"{KICK_AUTH_URL}?response_type=code"
            f"&client_id={self.client_id}"
            f"&redirect_uri={self.redirect_uri}"
            f"&scope={scopes}"
            f"&code_challenge={challenge}"
            f"&code_challenge_method=S256"
            f"&state=random"
        )

    def _exchange_code(self, code: str, verifier: str) -> dict:
        response = requests.post(
            KICK_TOKEN_URL,
            data={
                "grant_type": "authorization_code",
                "client_id": self.client_id,
                "client_secret": self.client_secret,
                "code": code,
                "code_verifier": verifier,
                "redirect_uri": self.redirect_uri,
            },
        )
        response.raise_for_status()
        return response.json()

    def is_authenticated(self) -> bool:
        tokens = self.storage.load()
        return bool(tokens and (tokens.get("access_token") or tokens.get("refresh_token")))

    def logout(self) -> None:
        self.storage.clear()

    REQUIRED_SCOPES = {
        "user:read": "dashboard.banner.scope.kick_user_read",
        "channel:read": "dashboard.banner.scope.kick_channel_read",
        "channel:write": "dashboard.banner.scope.kick_channel_write",
        "channel:rewards:read": "dashboard.banner.scope.kick_channel_rewards_read",
        "channel:rewards:write": "dashboard.banner.scope.kick_channel_rewards_write",
        "chat:write": "dashboard.banner.scope.kick_chat_write",
        "moderation:ban": "dashboard.banner.scope.kick_moderation_ban",
        "moderation:chat_message:manage": "dashboard.banner.scope.kick_moderation_chat",
    }

    def get_missing_scopes(self) -> list[str]:
        tokens = self.storage.load()
        if not tokens or not (tokens.get("access_token") or tokens.get("refresh_token")):
            return []

        raw_scopes = tokens.get("scope", "")
        if isinstance(raw_scopes, list):
            current_scopes = set(raw_scopes)
        else:
            current_scopes = set(raw_scopes.split())

        return [
            i18n_key
            for scope, i18n_key in self.REQUIRED_SCOPES.items()
            if scope not in current_scopes
        ]

    def has_missing_scopes(self) -> bool:
        return len(self.get_missing_scopes()) > 0

class TwitchAuthManager:
    def __init__(self, client_id: str, client_secret: str, redirect_uri: str, storage: TokenStorage, success_html_path: str = "") -> None:
        self.client_id = client_id
        self.client_secret = client_secret
        self.redirect_uri = redirect_uri
        self.storage = storage
        self.success_html_path = success_html_path

    def get_tokens(self, force: bool = False) -> dict:
        if force:
            return self.login(force=True)
        tokens = self.storage.load()
        if tokens and "access_token" in tokens:
            return tokens
        return {}

    def login(self, force: bool = False) -> dict:
        if not force:
            tokens = self.get_tokens(force=False)
            if tokens and tokens.get("access_token"):
                return tokens
        return self._new_login(force=force)

    def is_authenticated(self) -> bool:
        tokens = self.storage.load()
        return bool(tokens and (tokens.get("access_token") or tokens.get("refresh_token")))

    def refresh_token(self) -> dict:
        tokens = self.storage.load()
        refresh_token = tokens.get("refresh_token") if tokens else None

        if not refresh_token:
            return {}

        if not self.client_secret:
            raise ValueError("Falta el TWITCH_CLIENT_SECRET en backend/config/api_keys.py.")

        try:
            response = requests.post(
                TWITCH_TOKEN_URL,
                data={
                    "grant_type": "refresh_token",
                    "client_id": self.client_id,
                    "client_secret": self.client_secret,
                    "refresh_token": refresh_token,
                },
                timeout=10,
            )
            response.raise_for_status()
            new_tokens = response.json()
            if "refresh_token" not in new_tokens and refresh_token:
                new_tokens["refresh_token"] = refresh_token
            self.storage.save(new_tokens)
            return new_tokens
        except requests.exceptions.RequestException as e:
            logger.warning("[TwitchAuth] Fallo al refrescar token de Twitch: %s", e)
            self.logout()
            raise e

    def _new_login(self, force: bool = False) -> dict:
        scopes = "chat:read chat:edit user:read:chat user:write:chat channel:moderate moderator:manage:chat_messages moderator:manage:banned_users channel:manage:broadcast channel:read:redemptions channel:manage:redemptions moderator:read:followers"
        force_param = "&force_verify=true" if force else ""
        auth_url = (
            f"{TWITCH_AUTH_URL}?response_type=code"
            f"&client_id={self.client_id}"
            f"&redirect_uri={self.redirect_uri}"
            f"&scope={scopes}"
            f"&state=random"
            f"{force_param}"
        )
        port = int(urlparse(self.redirect_uri).port or 8080)
        auth_code = OAuthCallbackServer.capture_auth_code(auth_url, port, self.success_html_path, provider="twitch")

        if not auth_code:
            raise TimeoutError("Auth timeout or user canceled login.")

        tokens = self._exchange_code(auth_code)
        self.storage.save(tokens)
        return tokens

    def _exchange_code(self, code: str) -> dict:
        if not self.client_secret:
            raise ValueError("Falta el TWITCH_CLIENT_SECRET en backend/config/api_keys.py. Twitch requiere un Client Secret válido para el flujo OAuth.")

        response = requests.post(
            TWITCH_TOKEN_URL,
            data={
                "grant_type": "authorization_code",
                "client_id": self.client_id,
                "client_secret": self.client_secret,
                "code": code,
                "redirect_uri": self.redirect_uri,
            },
        )
        if response.status_code != 200:
            try:
                err_json = response.json()
                msg = err_json.get("message", response.text)
            except Exception:
                msg = response.text
            raise ValueError(f"Error {response.status_code} de Twitch: {msg}")
        return response.json()

    def logout(self) -> None:
        self.storage.clear()

    REQUIRED_TWITCH_SCOPES = {
        "chat:read": "dashboard.banner.scope.twitch_chat_read",
        "chat:edit": "dashboard.banner.scope.twitch_chat_edit",
        "user:read:chat": "dashboard.banner.scope.twitch_user_read_chat",
        "user:write:chat": "dashboard.banner.scope.twitch_user_write_chat",
        "channel:moderate": "dashboard.banner.scope.twitch_channel_moderate",
        "moderator:manage:chat_messages": "dashboard.banner.scope.twitch_moderation_chat",
        "moderator:manage:banned_users": "dashboard.banner.scope.twitch_moderation_ban",
        "channel:manage:broadcast": "dashboard.banner.scope.twitch_channel_manage_broadcast",
        "channel:read:redemptions": "dashboard.banner.scope.twitch_channel_read_redemptions",
        "channel:manage:redemptions": "dashboard.banner.scope.twitch_channel_manage_redemptions",
        "moderator:read:followers": "dashboard.banner.scope.twitch_moderator_read_followers",
    }

    def get_missing_scopes(self) -> list[str]:
        tokens = self.storage.load()
        if not tokens or not (tokens.get("access_token") or tokens.get("refresh_token")):
            return []

        raw_scopes = tokens.get("scope", "")
        if isinstance(raw_scopes, list):
            scopes_set = set(raw_scopes)
        else:
            scopes_set = set(raw_scopes.split())

        return [
            i18n_key
            for scope, i18n_key in self.REQUIRED_TWITCH_SCOPES.items()
            if scope not in scopes_set
        ]

    def has_missing_scopes(self) -> bool:
        return len(self.get_missing_scopes()) > 0
