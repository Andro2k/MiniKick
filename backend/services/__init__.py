# backend\services\__init__.py

from .auth.oauth_service import AuthManager, OAuthCallbackServer
from .chat.chat_service import ChatService
from .chat.command_service import CommandService
from .chat.pipeline import ChatMessageDTO, MessagePipeline
from .chat.spam_service import SpamService
from .chat.timer_service import TimerService
from .rewards.media_trigger import MediaTriggerService
from .rewards.overlay_server import OverlayServerManager
from .rewards.rewards_service import RewardsService
from .system.dashboard_service import AvatarService
from .system.backup_service import BackupService
from .system.instance_services import SocketInstanceProvider
from .system.log_service import LogService
from .system.network_service import NetworkService
from .system.settings_service import SettingsService
from .system.translation_service import TranslationService
from .system.updater_service import GithubUpdateProvider, WindowsInstaller, UpdateManager

__all__ = [
    "AuthManager",
    "OAuthCallbackServer",
    "ChatService",
    "CommandService",
    "ChatMessageDTO",
    "MessagePipeline",
    "SpamService",
    "TimerService",
    "MediaTriggerService",
    "OverlayServerManager",
    "RewardsService",
    "AvatarService",
    "BackupService",
    "SocketInstanceProvider",
    "LogService",
    "NetworkService",
    "SettingsService",
    "TranslationService",
    "GithubUpdateProvider",
    "WindowsInstaller",
    "UpdateManager"
]
