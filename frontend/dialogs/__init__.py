# frontend\dialogs\__init__.py

from .base_dialog import (ModernFramelessShell, ModernModalRewards, 
                           ModernWizardPanel, ModernConfirmDialog)
from .update_dialog import UpdateDialog
from .rewards_dialog import RewardsConfigWizard
from .visual_positioner_dialog import VisualPositionerDialog
from .command_dialog import CommandConfigWizard

__all__ = [
    "ModernFramelessShell",
    "ModernModalRewards",
    "ModernWizardPanel",
    "ModernConfirmDialog",
    "UpdateDialog",
    "VisualPositionerDialog",
    "RewardsConfigWizard",
    "CommandConfigWizard"
]