# backend/services/system/__init__.py

from .backup_service import BackupService
from .dashboard_service import AvatarService
from .instance_services import SocketInstanceProvider
from .log_service import LogService
from .settings_service import SettingsService
from .translation_service import TranslationService
from .updater_service import GithubUpdateProvider, WindowsInstaller, UpdateManager
from .widget_service import WidgetService

__all__ = [
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
