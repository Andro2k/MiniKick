# backend\storage\token_storage.py

from backend.database.manager import DatabaseManager

class SQLiteTokenStorage:
    def __init__(self, db_manager: DatabaseManager, provider: str = "kick"):
        self.db_manager = db_manager
        self.provider = provider

    def load(self) -> dict | None:
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

    def save(self, tokens: dict) -> None:
        with self.db_manager.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM tokens WHERE provider = ?", (self.provider,))
            cursor.execute(
                "INSERT INTO tokens (provider, access_token, refresh_token, expires_in, scope, token_type) VALUES (?, ?, ?, ?, ?, ?)", 
                (self.provider, tokens.get("access_token"), tokens.get("refresh_token"), tokens.get("expires_in"), tokens.get("scope"), tokens.get("token_type"))
            )
            conn.commit()

    def clear(self) -> None:
        with self.db_manager.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM tokens WHERE provider = ?", (self.provider,))
            conn.commit()
