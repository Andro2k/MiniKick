# backend\services\__init__.py
"""Servicios de las distintas áreas de la aplicación."""

from .alerts import AlertService, AlertQueue
from .auth import BaseOAuthManager, KickAuthManager, TwitchAuthManager, OAuthCallbackServer
from .chat import (
    ChatService,
    CommandService,
    ChatMessageDTO,
    MessagePipeline,
    SpamService,
    TimerService,
)
from .voice import PiperVoiceManager, PiperVoiceDownloadWorker, DEFAULT_PIPER_VOICE_ID, TTSManager
from .media import GiphyService
from .overlay import OverlayServerManager, WebSocketClient
from .rewards import RewardsService, generate_media_thumbnail
from .schedule import ScheduleService
from .media import AvatarService
from .app import BackupService, BrowserService, SocketInstanceProvider
from .updates import GithubUpdateProvider, UpdateManager, WhatsNewService, WindowsInstaller
from .logs import LogService
from .settings import SettingsService, TranslationService, WidgetService

__all__ = [
    "AlertService",
    "AlertQueue",
    "BaseOAuthManager",
    "KickAuthManager",
    "TwitchAuthManager",
    "OAuthCallbackServer",
    "ChatService",
    "CommandService",
    "ChatMessageDTO",
    "MessagePipeline",
    "PiperVoiceManager",
    "PiperVoiceDownloadWorker",
    "DEFAULT_PIPER_VOICE_ID",
    "SpamService",
    "TimerService",
    "TTSManager",
    "GiphyService",
    "OverlayServerManager",
    "WebSocketClient",
    "RewardsService",
    "generate_media_thumbnail",
    "ScheduleService",
    "AvatarService",
    "BackupService",
    "BrowserService",
    "GithubUpdateProvider",
    "LogService",
    "SettingsService",
    "SocketInstanceProvider",
    "TranslationService",
    "UpdateManager",
    "WhatsNewService",
    "WidgetService",
    "WindowsInstaller",
]
