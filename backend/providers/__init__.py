# backend\providers\__init__.py

from .chat.kick_client import KickAPIClient
from .chat.kick_websocket import ChatSocketManager
from .music.spotify_client import SpotifyAuthManager, SpotifyMusicProvider
from .music.youtube_client import YouTubeMusicProvider
from .voices.tts_local import LocalTTSProvider
from .voices.tts_online import WebTTSProvider
from .voices.tts_service import TTSManager

__all__ = [
    "KickAPIClient",
    "ChatSocketManager",
    "SpotifyAuthManager",
    "SpotifyMusicProvider",
    "YouTubeMusicProvider",
    "LocalTTSProvider",
    "WebTTSProvider",
    "TTSManager"
]
