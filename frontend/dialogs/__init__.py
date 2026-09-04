# frontend\dialogs\__init__.py

from .base_dialog import ModernFramelessShell, ModernModal, ModernWizardPanel, ModernConfirmDialog
from .already_running_dialog import AlreadyRunningDialog
from .bug_report_dialog import BugReportDialog
from .crash_report_dialog import CrashReportDialog
from .update_dialog import UpdateDialog
from .release_notes_dialog import ReleaseNotesDialog
from .rewards_dialog import RewardsConfigWizard
from .timer_dialog import TimerConfigWizard, MessageEditorDialog
from .visual_positioner_dialog import VisualPositionerDialog
from .command_dialog import CommandConfigWizard
from .piper_voices_dialog import PiperVoicesDialog
from .youtube_connect_dialog import YouTubeConnectDialog
from .tiktok_connect_dialog import TikTokConnectDialog

__all__ = [
    "ModernFramelessShell",
    "ModernModal",
    "ModernWizardPanel",
    "ModernConfirmDialog",
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