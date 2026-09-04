# backend/services/__init__.py

from .alerts import AlertService, AlertQueue
from .auth import KickAuthManager, TwitchAuthManager, OAuthCallbackServer
from .chat import (
    ChatService,
    CommandService,
    ChatMessageDTO,
    MessagePipeline,
    PiperVoiceManager,
    SpamService,
    TimerService,
    TTSManager,
)
from .overlay import OverlayServerManager, WebSocketClient
from .rewards import RewardsService, generate_media_thumbnail
from .schedule import ScheduleService
from .system import (
    AvatarService,
    BackupService,
    GithubUpdateProvider,
    LogService,
    SettingsService,
    SocketInstanceProvider,
    TranslationService,
    UpdateManager,
    WidgetService,
    WindowsInstaller,
)

__all__ = [
    "AlertService",
    "AlertQueue",
    "KickAuthManager",
    "TwitchAuthManager",
    "OAuthCallbackServer",
    "ChatService",
    "CommandService",
    "ChatMessageDTO",
    "MessagePipeline",
    "PiperVoiceManager",
    "SpamService",
    "TimerService",
    "TTSManager",
    "OverlayServerManager",
    "WebSocketClient",
    "RewardsService",
    "generate_media_thumbnail",
    "ScheduleService",
    "AvatarService",
    "BackupService",
    "GithubUpdateProvider",
    "LogService",
    "SettingsService",
    "SocketInstanceProvider",
    "TranslationService",
    "UpdateManager",
    "WidgetService",
    "WindowsInstaller",
]
