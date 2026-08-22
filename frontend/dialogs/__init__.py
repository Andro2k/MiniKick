# frontend\dialogs\__init__.py

from .base_dialog import ModernFramelessShell, ModernModal, ModernWizardPanel, ModernConfirmDialog
from .update_dialog import UpdateDialog
from .release_notes_dialog import ReleaseNotesDialog
from .rewards_dialog import RewardsConfigWizard
from .visual_positioner_dialog import VisualPositionerDialog
from .command_dialog import CommandConfigWizard
from .piper_voices_dialog import PiperVoicesDialog

__all__ = [
    "ModernFramelessShell",
    "ModernModal",
    "ModernWizardPanel",
    "ModernConfirmDialog",
    "UpdateDialog",
    "ReleaseNotesDialog",
    "VisualPositionerDialog",
    "RewardsConfigWizard",
    "CommandConfigWizard",
    "PiperVoicesDialog"
]