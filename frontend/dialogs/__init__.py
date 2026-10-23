# frontend\dialogs\__init__.py

from typing import TYPE_CHECKING

_EXPORTS = {
    "ModernFramelessShell": ".base_dialog",
    "ModernModal": ".base_dialog",
    "ModernWizardPanel": ".base_dialog",
    "ModernConfirmDialog": ".base_dialog",
    "PlatformConnectDialog": ".platform_dialog",
    "AlreadyRunningDialog": ".already_running_dialog",
    "BugReportDialog": ".bug_report_dialog",
    "CrashReportDialog": ".crash_report_dialog",
    "UpdateDialog": ".updater_dialog",
    "ReleaseNotesDialog": ".release_notes_dialog",
    "VisualPositionerDialog": ".positioner_dialog",
    "RewardsConfigWizard": ".rewards_dialog",
    "TimerConfigWizard": ".timers_dialog",
    "MessageEditorDialog": ".message_dialog",
    "CommandConfigWizard": ".commands_dialog",
    "PiperVoicesDialog": ".piper_dialog",
    "YouTubeConnectDialog": ".youtube_dialog",
    "TikTokConnectDialog": ".tiktok_dialog",
    "DuplicateAlertModal": ".duplicate_alert_dialog",
    "ImportBackupModal": ".import_backup_dialog",
    "WhatsNewDialog": ".whats_new_dialog",
    "SplashScreen": ".splash_screen",
}

__all__ = list(_EXPORTS)


def __getattr__(name: str):
    if name in _EXPORTS:
        import importlib

        module = importlib.import_module(_EXPORTS[name], package=__name__)
        value = getattr(module, name)
        globals()[name] = value
        return value
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


if TYPE_CHECKING:
    from .already_running_dialog import AlreadyRunningDialog
    from .bug_report_dialog import BugReportDialog
    from .commands_dialog import CommandConfigWizard
    from .crash_report_dialog import CrashReportDialog
    from .duplicate_alert_dialog import DuplicateAlertModal
    from .import_backup_dialog import ImportBackupModal
    from .message_dialog import MessageEditorDialog
    from .base_dialog import ModernConfirmDialog, ModernFramelessShell, ModernModal, ModernWizardPanel
    from .piper_dialog import PiperVoicesDialog
    from .platform_dialog import PlatformConnectDialog
    from .positioner_dialog import VisualPositionerDialog
    from .release_notes_dialog import ReleaseNotesDialog
    from .rewards_dialog import RewardsConfigWizard
    from .splash_screen import SplashScreen
    from .tiktok_dialog import TikTokConnectDialog
    from .timers_dialog import TimerConfigWizard
    from .updater_dialog import UpdateDialog
    from .whats_new_dialog import WhatsNewDialog
    from .youtube_dialog import YouTubeConnectDialog
