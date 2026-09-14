# backend\interfaces\__init__.py

from .i_auth import TokenStorage, TokenProvider
from .i_instance import SingleInstanceProvider
from .i_settings import SettingsStorage
from .i_tts import ITTSProvider
from .i_updater import IUpdateChecker, IUpdateDownloader, IUpdateInstaller
from .i_music_provider import IMusicProvider
from .i_chat_service import IChatService
from .i_chat_provider import IChatProvider
from .i_alerts import AlertStorageProtocol
from .i_browser import IBrowserService

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
    "AlertStorageProtocol",
    "IBrowserService",
]