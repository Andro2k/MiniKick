# backend\interfaces\__init__.py

from .auth_interfaces import TokenStorage, TokenProvider
from .instance_interfaces import SingleInstanceProvider
from .music_interfaces import MusicPlayerProvider
from .settings_interfaces import SettingsStorage
from .tts_interfaces import ITTSProvider
from .updater_interfaces import IUpdateChecker, IUpdateDownloader, IUpdateInstaller

__all__ = [
    "TokenStorage",
    "TokenProvider",
    "SingleInstanceProvider",
    "MusicPlayerProvider",
    "SettingsStorage",
    "ITTSProvider",
    "IUpdateChecker",
    "IUpdateDownloader",
    "IUpdateInstaller"
]