# backend\interfaces\__init__.py

from .auth_interfaces import TokenStorage, TokenProvider
from .instance_interfaces import SingleInstanceProvider
from .music_interfaces import MusicPlayerProvider
from .settings_interfaces import SettingsStorage
from .tts_interfaces import ITTSProvider
from .updater_interfaces import IUpdateChecker, IUpdateDownloader, IUpdateInstaller
from .music_provider import IMusicProvider
from .storage_repository import IStorageRepository
from .chat_service import IChatService

__all__ = [
    "TokenStorage",
    "TokenProvider",
    "SingleInstanceProvider",
    "MusicPlayerProvider",
    "SettingsStorage",
    "ITTSProvider",
    "IUpdateChecker",
    "IUpdateDownloader",
    "IUpdateInstaller",
    "IMusicProvider",
    "IStorageRepository",
    "IChatService",
]