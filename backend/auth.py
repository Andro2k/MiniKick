# backend/auth.py

import base64
import hashlib
import json
import os
import webbrowser
from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import parse_qs, urlparse

import requests
from backend.interfaces.auth_interfaces import TokenStorage

KICK_AUTH_URL = "https://id.kick.com/oauth/authorize"
KICK_TOKEN_URL = "https://id.kick.com/oauth/token"

# --- Capa de Acceso a Datos ---
class FileTokenStorage:
    def __init__(self, filepath: str = "token.json"):
        self.filepath = filepath

    def load(self) -> dict | None:
        if os.path.exists(self.filepath):
            with open(self.filepath, "r") as f:
                return json.load(f)
        return None

    def save(self, tokens: dict) -> None:
        with open(self.filepath, "w") as f:
            json.dump(tokens, f)

# --- Capa de Presentación / Red ---
class _OAuthCallbackHandler(BaseHTTPRequestHandler):
    def do_GET(self) -> None:
        query = parse_qs(urlparse(self.path).query)
        if "code" in query:
            self.server.auth_code = query["code"][0]  # type: ignore[attr-defined]
            self.send_response(200)
            self.send_header("Content-type", "text/html")
            self.end_headers()
            
            # Buscamos la ruta inyectada en el servidor
            html_path = getattr(self.server, "success_html_path", "")
            try:
                with open(html_path, "rb") as f:
                    self.wfile.write(f.read())
            except FileNotFoundError:
                self.wfile.write("<h1>Autenticación exitosa. Puedes cerrar esta pestaña.</h1>".encode("utf-8"))

    def log_message(self, *args) -> None:
        pass

class OAuthCallbackServer:
    @staticmethod
    def capture_auth_code(url: str, port: int, success_html_path: str) -> str:
        httpd = HTTPServer(("", port), _OAuthCallbackHandler)
        httpd.auth_code = None  # type: ignore[attr-defined]
        httpd.success_html_path = success_html_path # INYECCIÓN DE DEPENDENCIA
        webbrowser.open(url)
        while httpd.auth_code is None:
            httpd.handle_request()
        httpd.server_close()
        return httpd.auth_code  # type: ignore[attr-defined]

# --- Lógica de Negocio ---
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
            # Si el refresh falla (fue revocado o expiró), forzamos un nuevo inicio de sesión
            return self._new_login()

    def _new_login(self) -> dict:
        verifier, challenge = self._pkce_pair()
        auth_url = self._build_auth_url(challenge)

        port = int(urlparse(self.redirect_uri).port or 8080)
        auth_code = OAuthCallbackServer.capture_auth_code(auth_url, port, self.success_html_path)

        tokens = self._exchange_code(auth_code, verifier)
        self.storage.save(tokens)
        return tokens

    @staticmethod
    def _pkce_pair() -> tuple[str, str]:
        verifier = base64.urlsafe_b64encode(os.urandom(32)).decode().rstrip("=")
        challenge = base64.urlsafe_b64encode(hashlib.sha256(verifier.encode()).digest()).decode().rstrip("=")
        return verifier, challenge

    def _build_auth_url(self, challenge: str) -> str:
        return (
            f"{KICK_AUTH_URL}?response_type=code"
            f"&client_id={self.client_id}"
            f"&redirect_uri={self.redirect_uri}"
            f"&scope=user:read"
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
    
    # NUEVO MÉTODO
    def logout(self) -> None:
        """Limpia las credenciales almacenadas"""
        self.storage.clear()
        # Opcional: Si Kick tuviera un endpoint de "revoke token", se llamaría aquí.