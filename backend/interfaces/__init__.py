# backend\interfaces\__init__.py

from .i_auth import TokenStorage, TokenProvider
from .i_settings import SettingsStorage
from .i_tts import ITTSProvider
from .i_updater import IUpdateChecker, IUpdateDownloader, IUpdateInstaller
from .i_music_provider import IMusicProvider
from .i_alerts import AlertStorageProtocol

__all__ = [
    "TokenStorage",
    "TokenProvider",
    "SettingsStorage",
    "ITTSProvider",
    "IUpdateChecker",
    "IUpdateDownloader",
    "IUpdateInstaller",
    "IMusicProvider",
    "AlertStorageProtocol",
]