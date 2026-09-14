# backend/services/system/__init__.py

from .backup_service import BackupService
from .browser_service import BrowserService
from .dashboard_service import AvatarService
from .instance_service import SocketInstanceProvider
from .logs_service import LogService
from .settings_service import SettingsService
from .translation_service import TranslationService
from .updater_service import GithubUpdateProvider, WindowsInstaller, UpdateManager
from .widgets_service import WidgetService

__all__ = [
    "AvatarService",
    "BackupService",
    "BrowserService",
    "GithubUpdateProvider",
    "LogService",
    "SettingsService",
    "SocketInstanceProvider",
    "TranslationService",
    "UpdateManager",
    "WidgetService",
    "WindowsInstaller",
]
