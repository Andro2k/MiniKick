# backend\services\auth\oauth_service.py

import base64
import hashlib
import hmac
import html
import logging
import os
import secrets
import time
from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import parse_qs, urlparse
import requests
from backend.interfaces import TokenStorage, TransientAuthError

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
        received_state = query.get("state", [None])[0]
        expected_state = getattr(self.server, "expected_state", None)

        if code or error:
            if expected_state and not self._state_matches(received_state, expected_state):
                logger.warning("[OAuthCallback] Ignored %s callback: invalid or missing OAuth state (possible CSRF).",
                               getattr(self.server, "provider", "kick"))
                self._reject_invalid_state()
                return

            self.server.auth_code = code or ""

            self.send_response(200)
            self.send_header("Content-type", "text/html; charset=utf-8")
            self.end_headers()

            html_path = getattr(self.server, "success_html_path", "")
            provider = getattr(self.server, "provider", "kick")
            success = bool(code)
            status = "success" if success else "error"
            if error:
                error_msg = query.get("error_description", [error])[0] if query.get("error_description") else error
            else:
                error_msg = ""

            provider_safe = html.escape(str(provider))
            status_safe = html.escape(str(status))
            error_msg_safe = html.escape(str(error_msg))

            content = None
            if html_path and os.path.exists(html_path):
                try:
                    with open(html_path, "r", encoding="utf-8") as f:
                        template = f.read()
                    content = template.replace("{{PROVIDER}}", provider_safe)
                    content = content.replace("{{STATUS}}", status_safe)
                    content = content.replace("{{ERROR_MSG}}", error_msg_safe)
                except Exception as e:
                    logger.warning("[OAuthCallback] Error reading auth template '%s': %s", html_path, e)

            if not content:
                status_text = "exitosa" if success else "fallida"
                status_en = "successful" if success else "failed"
                content = f"<h1>Autenticación {status_text} / Authentication {status_en}.</h1>"
                if error_msg_safe:
                    content += f"<p>Error: {error_msg_safe}</p>"

            try:
                self.wfile.write(content.encode("utf-8"))
            except (BrokenPipeError, ConnectionResetError):
                pass

    def log_message(self, *args) -> None:
        pass

    @staticmethod
    def _state_matches(received: str | None, expected: str) -> bool:
        return bool(received) and hmac.compare_digest(str(received), str(expected))

    def _reject_invalid_state(self) -> None:
        self.send_response(400)
        self.send_header("Content-type", "text/plain; charset=utf-8")
        self.end_headers()
        try:
            self.wfile.write(b"Invalid OAuth state parameter.")
        except (BrokenPipeError, ConnectionResetError):
            pass

class OAuthCallbackServer:
    @staticmethod
    def capture_auth_code(
        url: str,
        port: int,
        success_html_path: str,
        timeout_seconds: int = 120,
        provider: str = "kick",
        browser_service=None,
        expected_state: str | None = None,
    ) -> str | None:
        try:
            httpd = HTTPServer(("127.0.0.1", port), _OAuthCallbackHandler)
        except OSError as e:
            logger.error("[OAuthCallbackServer] Cannot bind port %d for %s auth: %s", port, provider, e)
            raise OSError(f"Port {port} is already in use by another authentication process.") from e
        httpd.timeout = 1 
        httpd.auth_code = None
        httpd.success_html_path = success_html_path
        httpd.provider = provider
        httpd.expected_state = expected_state
        
        opened = False
        if browser_service and hasattr(browser_service, "open_url"):
            opened = browser_service.open_url(url)
        if not opened:
            from backend.services.system.browser_service import BrowserService
            BrowserService._open_default(url)
        start_time = time.time()
        
        while httpd.auth_code is None:
            if time.time() - start_time > timeout_seconds:
                break
            httpd.handle_request()
            
        httpd.server_close()
        return httpd.auth_code

class BaseOAuthManager:
    REQUIRED_SCOPES: dict[str, str] = {}

    @staticmethod
    def _classify_refresh_error(error: requests.exceptions.RequestException) -> str:
        if isinstance(error, requests.exceptions.HTTPError) and error.response is not None:
            return "invalid" if error.response.status_code in (400, 401) else "transient"
        return "transient"

    def __init__(
        self,
        client_id: str,
        client_secret: str,
        redirect_uri: str,
        storage: TokenStorage,
        success_html_path: str = "",
        browser_service=None,
    ) -> None:
        self.client_id = client_id
        self.client_secret = client_secret
        self.redirect_uri = redirect_uri
        self.storage = storage
        self.success_html_path = success_html_path
        self.browser_service = browser_service

    def get_tokens(self, force: bool = False) -> dict:
        if force:
            return self.login(force=True)
        tokens = self.storage.load()
        if tokens and "access_token" in tokens:
            return tokens
        return {}

    def is_authenticated(self) -> bool:
        tokens = self.storage.load()
        return bool(tokens and (tokens.get("access_token") or tokens.get("refresh_token")))

    def logout(self) -> None:
        self.storage.clear()

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


class KickAuthManager(BaseOAuthManager):
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

    def login(self, force: bool = False) -> dict:
        if not force:
            tokens = self.get_tokens(force=False)
            if tokens and tokens.get("access_token"):
                return tokens
        return self._new_login()

    def refresh_token(self) -> dict:
        tokens = self.storage.load()
        refresh_token = tokens.get("refresh_token") if tokens else None

        if not refresh_token:
            return {}

        try:
            response = requests.post(
                KICK_TOKEN_URL,
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
            self.storage.save(new_tokens)
            return new_tokens
        except requests.exceptions.RequestException as e:
            if self._classify_refresh_error(e) == "invalid":
                logger.warning("[KickAuth] Refresh token rejected (invalid/expired). Clearing session: %s", e)
                self.logout()
                return {}
            logger.warning("[KickAuth] Transient error refreshing token; keeping session: %s", e)
            raise TransientAuthError(str(e)) from e

    def _new_login(self) -> dict:
        verifier, challenge = self._pkce_pair()
        state = secrets.token_urlsafe(32)
        auth_url = self._build_auth_url(challenge, state)

        port = int(urlparse(self.redirect_uri).port or 8080)
        auth_code = OAuthCallbackServer.capture_auth_code(
            auth_url, port, self.success_html_path, provider="kick",
            browser_service=self.browser_service, expected_state=state
        )

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

    def _build_auth_url(self, challenge: str, state: str) -> str:
        scopes = "user:read channel:read channel:write channel:rewards:read channel:rewards:write chat:write moderation:ban moderation:chat_message:manage"
        return (
            f"{KICK_AUTH_URL}?response_type=code"
            f"&client_id={self.client_id}"
            f"&redirect_uri={self.redirect_uri}"
            f"&scope={scopes}"
            f"&code_challenge={challenge}"
            f"&code_challenge_method=S256"
            f"&state={state}"
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
            timeout=10,
        )
        response.raise_for_status()
        return response.json()


class TwitchAuthManager(BaseOAuthManager):
    REQUIRED_SCOPES = {
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
    REQUIRED_TWITCH_SCOPES = REQUIRED_SCOPES

    def login(self, force: bool = False) -> dict:
        if not force:
            tokens = self.get_tokens(force=False)
            if tokens and tokens.get("access_token"):
                return tokens
        return self._new_login(force=force)

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
            if self._classify_refresh_error(e) == "invalid":
                logger.warning("[TwitchAuth] Refresh token rejected (invalid/expired). Clearing session: %s", e)
                self.logout()
                return {}
            logger.warning("[TwitchAuth] Transient error refreshing token; keeping session: %s", e)
            raise TransientAuthError(str(e)) from e

    def _new_login(self, force: bool = False) -> dict:
        scopes = "chat:read chat:edit user:read:chat user:write:chat channel:moderate moderator:manage:chat_messages moderator:manage:banned_users channel:manage:broadcast channel:read:redemptions channel:manage:redemptions moderator:read:followers"
        force_param = "&force_verify=true" if force else ""
        state = secrets.token_urlsafe(32)
        auth_url = (
            f"{TWITCH_AUTH_URL}?response_type=code"
            f"&client_id={self.client_id}"
            f"&redirect_uri={self.redirect_uri}"
            f"&scope={scopes}"
            f"&state={state}"
            f"{force_param}"
        )
        port = int(urlparse(self.redirect_uri).port or 8080)
        auth_code = OAuthCallbackServer.capture_auth_code(
            auth_url, port, self.success_html_path, provider="twitch",
            browser_service=self.browser_service, expected_state=state
        )

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
            timeout=10,
        )
        if response.status_code != 200:
            try:
                err_json = response.json()
                msg = err_json.get("message", response.text)
            except Exception:
                msg = response.text
            raise ValueError(f"Error {response.status_code} de Twitch: {msg}")
        return response.json()
