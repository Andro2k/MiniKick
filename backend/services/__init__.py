# backend\services\__init__.py

from .auth.oauth_service import KickAuthManager, TwitchAuthManager, OAuthCallbackServer
from .chat.chat_service import ChatService
from .chat.command_service import CommandService
from .chat.pipeline import ChatMessageDTO, MessagePipeline
from .chat.spam_service import SpamService
from .chat.timer_service import TimerService
from .chat.tts_service import TTSManager
from .overlay import OverlayServerManager
from .rewards.rewards_service import RewardsService
from .system.dashboard_service import AvatarService
from .system.backup_service import BackupService
from .system.instance_services import SocketInstanceProvider
from .system.log_service import LogService
from .system.settings_service import SettingsService
from .system.translation_service import TranslationService
from .system.updater_service import GithubUpdateProvider, WindowsInstaller, UpdateManager
from .system.widget_service import WidgetService
from .schedule.schedule_service import ScheduleService
from .alerts.alert_service import AlertService

__all__ = [
    "KickAuthManager",
    "TwitchAuthManager",
    "OAuthCallbackServer",
    "ChatService",
    "CommandService",
    "ChatMessageDTO",
    "MessagePipeline",
    "SpamService",
    "TimerService",
    "TTSManager",
    "OverlayServerManager",
    "RewardsService",
    "AvatarService",
    "BackupService",
    "SocketInstanceProvider",
    "LogService",
    "SettingsService",
    "TranslationService",
    "GithubUpdateProvider",
    "WindowsInstaller",
    "UpdateManager",
    "WidgetService",
    "ScheduleService",
    "AlertService"
]
