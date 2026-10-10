# backend\interfaces\i_auth.py

from typing import Protocol

class TokenStorage(Protocol):
    def load(self) -> dict | None: ...

    def save(self, tokens: dict) -> None: ...
    
    def clear(self) -> None: ...

class TokenProvider(Protocol):
    def get_tokens(self) -> dict: ...
    
    def refresh_token(self) -> dict: ...


class TransientAuthError(Exception):
    """Raised when a token refresh fails for a transient reason (network/timeout/5xx).

    Callers must keep the current session and retry later, as opposed to an invalid
    or revoked token, which requires re-authentication.
    """

    pass