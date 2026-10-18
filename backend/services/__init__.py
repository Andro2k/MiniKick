# backend/services/__init__.py

from .alerts import AlertService, AlertQueue
from .auth import BaseOAuthManager, KickAuthManager, TwitchAuthManager, OAuthCallbackServer
from .chat import (
    ChatService,
    CommandService,
    ChatMessageDTO,
    MessagePipeline,
    PiperVoiceManager,
    PiperVoiceDownloadWorker,
    DEFAULT_PIPER_VOICE_ID,
    SpamService,
    TimerService,
    TTSManager,
    GiphyService,
)
from .overlay import OverlayServerManager, WebSocketClient
from .rewards import RewardsService, generate_media_thumbnail
from .schedule import ScheduleService
from .system import (
    AvatarService,
    BackupService,
    BrowserService,
    GithubUpdateProvider,
    LogService,
    SettingsService,
    SocketInstanceProvider,
    TranslationService,
    UpdateManager,
    WhatsNewService,
    WidgetService,
    WindowsInstaller,
)

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
