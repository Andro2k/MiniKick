# backend\interfaces\auth_interface.py
"""Contratos para el almacenamiento y los proveedores de tokens, además del error temporal de autenticación."""

from typing import Protocol

class TokenStorage(Protocol):
    def load(self) -> dict | None: ...

    def save(self, tokens: dict) -> None: ...
    
    def clear(self) -> None: ...


class TokenProvider(Protocol):
    def get_tokens(self) -> dict: ...
    
    def refresh_token(self) -> dict: ...


class TransientAuthError(Exception):
    pass