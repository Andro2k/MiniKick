# frontend/components/dialogs/__init__.py

from .base_dialogs import (ModernFramelessShell, ModernModalAlert, 
                           ModernWizardPanel, ModernConfirmDialog)
from .update_dialog import UpdateDialog
from .alert_dialogs import AlertConfigWizard
from .visual_positioner_dialog import VisualPositionerDialog
from .command_dialogs import CommandConfigWizard

__all__ = [
    "ModernFramelessShell",
    "ModernModalAlert",
    "ModernWizardPanel",
    "ModernConfirmDialog",
    "UpdateDialog",
    "VisualPositionerDialog",
    "AlertConfigWizard",
    "CommandConfigWizard"
]