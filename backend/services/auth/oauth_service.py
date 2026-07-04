# backend\services\auth\oauth_service.py

import base64
import hashlib
import os
import time
import webbrowser
from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import parse_qs, urlparse
import requests
from backend.interfaces.auth_interfaces import TokenStorage

KICK_AUTH_URL = "https://id.kick.com/oauth/authorize"
KICK_TOKEN_URL = "https://id.kick.com/oauth/token"

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
            self.send_header("Content-type", "text/html")
            self.end_headers()
            
            html_path = getattr(self.server, "success_html_path", "")
            provider = getattr(self.server, "provider", "kick")
            
            try:
                with open(html_path, "r", encoding="utf-8") as f:
                    content = f.read()
                
                status = "success" if code else "error"
                error_msg = ""
                if error:
                    error_msg = query.get("error_description", [error])[0]
                
                content = content.replace("{{PROVIDER}}", provider)
                content = content.replace("{{STATUS}}", status)
                content = content.replace("{{ERROR_MSG}}", error_msg)
                
                self.wfile.write(content.encode("utf-8"))
            except FileNotFoundError:
                status_text = "exitoso" if code else "fallido"
                html_msg = f"<h1>Autenticación {status_text} / Authentication {status}.</h1>"
                if error:
                    error_desc = query.get("error_description", [error])[0]
                    html_msg += f"<p>Error: {error_desc}</p>"
                self.wfile.write(html_msg.encode("utf-8"))
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

    def get_tokens(self) -> dict:
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
        scopes = "user:read channel:rewards:read channel:rewards:write chat:write moderation:ban moderation:chat_message:manage"
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

    def logout(self) -> None:
        self.storage.clear()

    def get_missing_scopes(self) -> list[str]:
        tokens = self.storage.load()
        if not tokens:
            return []

        REQUIRED_SCOPES = {
            "moderation:ban": "dashboard.banner.scope.moderation_ban",
            "moderation:chat_message:manage": "dashboard.banner.scope.moderation_chat",
        }

        current_scopes = tokens.get("scope", "")
        return [
            i18n_key
            for scope, i18n_key in REQUIRED_SCOPES.items()
            if scope not in current_scopes
        ]

    def has_missing_scopes(self) -> bool:
        return len(self.get_missing_scopes()) > 0