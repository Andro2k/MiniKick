# backend\interfaces\__init__.py

from .auth_interfaces import TokenStorage, TokenProvider
from .instance_interfaces import SingleInstanceProvider
from .settings_interfaces import SettingsStorage
from .tts_interfaces import ITTSProvider
from .updater_interfaces import IUpdateChecker, IUpdateDownloader, IUpdateInstaller
from .music_provider import IMusicProvider
from .chat_service import IChatService
from .chat_provider import IChatProvider

__all__ = [
    "TokenStorage",
    "TokenProvider",
    "SingleInstanceProvider",
    "SettingsStorage",
    "ITTSProvider",
    "IUpdateChecker",
    "IUpdateDownloader",
    "IUpdateInstaller",
    "IMusicProvider",
    "IChatService",
    "IChatProvider",
]