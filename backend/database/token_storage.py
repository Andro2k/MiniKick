# backend\database\token_storage.py

import logging
from .manager import DatabaseManager

logger = logging.getLogger("minikick.database.token_storage")

class SQLiteTokenStorage:
    def __init__(self, db_manager: DatabaseManager, provider: str = "kick"):
        self.db_manager = db_manager
        self.provider = provider

    def load(self) -> dict | None:
        try:
            with self.db_manager.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "SELECT access_token, refresh_token, expires_in, scope, token_type FROM tokens WHERE provider = ? ORDER BY id DESC LIMIT 1",
                    (self.provider,)
                )
                row = cursor.fetchone()
                if row:
                    return {"access_token": row[0], "refresh_token": row[1], "expires_in": row[2], "scope": row[3], "token_type": row[4]}
                return None
        except Exception as e:
            logger.error("[TokenStorage] Error loading tokens for provider '%s': %s", self.provider, e)
            return None

    def save(self, tokens: dict) -> None:
        scope_val = tokens.get("scope")
        if isinstance(scope_val, list):
            scope_val = " ".join(scope_val)
        elif scope_val is None:
            scope_val = ""

        try:
            with self.db_manager.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("DELETE FROM tokens WHERE provider = ?", (self.provider,))
                cursor.execute(
                    "INSERT INTO tokens (provider, access_token, refresh_token, expires_in, scope, token_type) VALUES (?, ?, ?, ?, ?, ?)", 
                    (
                        self.provider,
                        tokens.get("access_token"),
                        tokens.get("refresh_token"),
                        tokens.get("expires_in"),
                        scope_val,
                        tokens.get("token_type")
                    )
                )
                conn.commit()
            logger.debug("[TokenStorage] Saved session tokens for provider: %s", self.provider)
        except Exception as e:
            logger.error("[TokenStorage] Error saving tokens for provider '%s': %s", self.provider, e)

    def clear(self) -> None:
        try:
            with self.db_manager.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("DELETE FROM tokens WHERE provider = ?", (self.provider,))
                conn.commit()
            logger.debug("[TokenStorage] Cleared session tokens for provider: %s", self.provider)
        except Exception as e:
            logger.error("[TokenStorage] Error clearing tokens for provider '%s': %s", self.provider, e)
