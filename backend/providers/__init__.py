# backend\providers\__init__.py

_LAZY_PROVIDERS = {
    "KickAPIClient": (".chat.kick_client", "KickAPIClient"),
    "ChatSocketManager": (".chat.kick_websocket", "ChatSocketManager"),
    "YouTubeMusicProvider": (".music.youtube_client", "YouTubeMusicProvider"),
    "LocalTTSProvider": (".voices.tts_local", "LocalTTSProvider"),
    "WebTTSProvider": (".voices.tts_online", "WebTTSProvider"),
    "PiperTTSProvider": (".voices.tts_piper", "PiperTTSProvider")
}

def __getattr__(name: str):
    if name in _LAZY_PROVIDERS:
        module_rel, attr = _LAZY_PROVIDERS[name]
        import importlib
        mod = importlib.import_module(module_rel, package=__name__)
        val = getattr(mod, attr)
        globals()[name] = val
        return val
    raise AttributeError(f"module '{__name__}' has no attribute '{name}'")

__all__ = list(_LAZY_PROVIDERS.keys())
