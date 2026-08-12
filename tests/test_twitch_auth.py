# tests\test_twitch_auth.py

from backend.services.auth.oauth_service import TwitchAuthManager

class DummyTokenStorage:
    def __init__(self, initial=None):
        self.data = initial or {}

    def load(self):
        return self.data

    def save(self, data):
        self.data = data

    def clear(self):
        self.data = {}

def test_twitch_auth_manager_missing_scopes():
    old_storage = DummyTokenStorage({
        "access_token": "old_token",
        "scope": "chat:read chat:edit user:read:chat channel:moderate"
    })
    manager = TwitchAuthManager("client_id", "client_secret", "http://localhost:8080/callback", old_storage)
    
    assert manager.has_missing_scopes()
    missing = manager.get_missing_scopes()
    assert "dashboard.banner.scope.twitch_moderation_chat" in missing
    assert "dashboard.banner.scope.twitch_moderation_ban" in missing

def test_twitch_auth_manager_full_scopes():
    full_storage = DummyTokenStorage({
        "access_token": "full_token",
        "scope": "chat:read chat:edit user:read:chat user:write:chat channel:moderate moderator:manage:chat_messages moderator:manage:banned_users"
    })
    manager = TwitchAuthManager("client_id", "client_secret", "http://localhost:8080/callback", full_storage)
    
    assert not manager.has_missing_scopes()
    assert len(manager.get_missing_scopes()) == 0

def test_twitch_auth_manager_logout():
    storage = DummyTokenStorage({"access_token": "token123"})
    manager = TwitchAuthManager("client_id", "client_secret", "http://localhost:8080/callback", storage)
    
    manager.logout()
    assert storage.load() == {}
