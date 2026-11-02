# backend\interfaces\__init__.py

from .i_auth import TokenStorage, TokenProvider, TransientAuthError
from .i_secrets import SecretCipher, TokenEncryptionError
from .i_config_provider import IConfigProvider
from .i_tts import ITTSProvider
from .i_updater import IUpdateChecker, IUpdateDownloader, IUpdateInstaller
from .i_music_provider import IMusicProvider
from .i_music_chat_context import IMusicChatContext
from .i_alerts import AlertStorageProtocol

__all__ = [
    "TokenStorage",
    "TokenProvider",
    "TransientAuthError",
    "SecretCipher",
    "IConfigProvider",
    "ITTSProvider",
    "IUpdateChecker",
    "IUpdateDownloader",
    "IUpdateInstaller",
    "IMusicProvider",
    "IMusicChatContext",
    "AlertStorageProtocol",
    "TokenEncryptionError",
]