# frontend\dialogs\__init__.py

from .base_dialog import ModernFramelessShell, ModernModal, ModernWizardPanel, ModernConfirmDialog
from .platform_dialog import PlatformConnectDialog
from .already_running_dialog import AlreadyRunningDialog
from .bug_report_dialog import BugReportDialog
from .crash_report_dialog import CrashReportDialog
from .updater_dialog import UpdateDialog
from .release_notes_dialog import ReleaseNotesDialog
from .rewards_dialog import RewardsConfigWizard
from .timers_dialog import TimerConfigWizard
from .message_dialog import MessageEditorDialog
from .positioner_dialog import VisualPositionerDialog
from .commands_dialog import CommandConfigWizard
from .piper_dialog import PiperVoicesDialog
from .youtube_dialog import YouTubeConnectDialog
from .tiktok_dialog import TikTokConnectDialog

__all__ = [
    "ModernFramelessShell",
    "ModernModal",
    "ModernWizardPanel",
    "ModernConfirmDialog",
    "PlatformConnectDialog",
    "AlreadyRunningDialog",
    "BugReportDialog",
    "CrashReportDialog",
    "UpdateDialog",
    "ReleaseNotesDialog",
    "VisualPositionerDialog",
    "RewardsConfigWizard",
    "TimerConfigWizard",
    "MessageEditorDialog",
    "CommandConfigWizard",
    "PiperVoicesDialog",
    "YouTubeConnectDialog",
    "TikTokConnectDialog"
]